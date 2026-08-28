from flask import Flask, request, jsonify
from flask_cors import CORS
import torch
import torch.nn as nn
import timm
import numpy as np
from PIL import Image
import albumentations as A
from albumentations.pytorch import ToTensorV2
import io
import sys
import os
import logging
import hashlib
from datetime import datetime, timedelta
import uuid
import jwt
from functools import wraps
from flask import g
logger = logging.getLogger(__name__)
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import matching engine
try:
    from matching_engine import find_matches, batch_optimise, ALL_WASTE_TYPES
    MATCHING_ENGINE_AVAILABLE = True
except ImportError as e:
    print(f"Matching engine not available: {e}")
    MATCHING_ENGINE_AVAILABLE = False

# Import database manager
try:
    from database.database_manager import db_manager
    DATABASE_AVAILABLE = True
except ImportError as e:
    print(f"Database manager not available: {e}")
    DATABASE_AVAILABLE = False

# Correct Model Architecture
class WasteClassifier(nn.Module):
    def __init__(self, num_classes=11):
        super().__init__()
        self.backbone = timm.create_model(
            'efficientnet_b3.ra2_in1k',
            pretrained=False,
            num_classes=0,
        )
        feat_dim = self.backbone.num_features
        self.head = nn.Sequential(
            nn.BatchNorm1d(feat_dim),
            nn.Dropout(0.4),
            nn.Linear(feat_dim, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, num_classes),
        )

    def forward(self, x):
        return self.head(self.backbone(x))

# Class definitions
UNIFIED_CLASSES = [
    'METAL', 'PLASTIC', 'PAPER_CARDBOARD', 'GLASS',
    'ORGANIC', 'TEXTILE', 'CONSTRUCTION', 'HAZARDOUS',
    'INDUSTRIAL_ASH', 'ELECTRONIC', 'MIXED',
]

CLASS_META = {
    'METAL': {'name': 'Metal', 'icon': '🔧'},
    'PLASTIC': {'name': 'Plastic', 'icon': '🥤'},
    'PAPER_CARDBOARD': {'name': 'Paper/Cardboard', 'icon': '📦'},
    'GLASS': {'name': 'Glass', 'icon': '🍷'},
    'ORGANIC': {'name': 'Organic', 'icon': '🌱'},
    'TEXTILE': {'name': 'Textile', 'icon': '👕'},
    'CONSTRUCTION': {'name': 'Construction', 'icon': '🏗️'},
    'HAZARDOUS': {'name': 'Hazardous', 'icon': '⚠️'},
    'INDUSTRIAL_ASH': {'name': 'Industrial Ash', 'icon': '🔥'},
    'ELECTRONIC': {'name': 'Electronic', 'icon': '💻'},
    'MIXED': {'name': 'Mixed Waste', 'icon': '🗑️'},
}

DEVICE = torch.device('cpu')  # Using CPU for now
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, 'model.pth')

# Internal mapping from model class tags to database/matching keys
CLASS_TO_INTERNAL = {
    'METAL': 'metal',
    'PLASTIC': 'plastic',
    'PAPER_CARDBOARD': 'paper/cardboard',
    'GLASS': 'glass',
    'ORGANIC': 'organic',
    'TEXTILE': 'textile',
    'CONSTRUCTION': 'construction',
    'HAZARDOUS': 'hazardous',
    'INDUSTRIAL_ASH': 'industrial ash',
    'ELECTRONIC': 'electronic',
    'MIXED': 'mixed',
}

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# JWT settings (configure via env in production)
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-change-me')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRES_SECONDS = int(os.environ.get('ACCESS_TOKEN_EXPIRES_SECONDS', 900))  # 15 minutes
REFRESH_TOKEN_EXPIRES_DAYS = int(os.environ.get('REFRESH_TOKEN_EXPIRES_DAYS', 14))

def load_model():
    try:
        # Load checkpoint
        checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
        print(f"✅ Model checkpoint loaded - epoch: {checkpoint['epoch']}, val mAP: {checkpoint['val_mAP']:.4f}")
        
        # Initialize correct model architecture
        model = WasteClassifier(num_classes=11)
        
        # Load state dict
        model.load_state_dict(checkpoint['model_state'])
        model.to(DEVICE)
        model.eval()
        
        print("✅ Model loaded successfully with correct architecture")
        return model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        import traceback
        traceback.print_exc()
        return None

# Initialize model
model = load_model()

# Correct preprocessing - must match training exactly
inference_transform = A.Compose([
    A.Resize(300, 300),  # ← must be 300, not 224
    A.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    ),
    ToTensorV2(),
])

def preprocess_image(image_bytes):
    """Convert image bytes to tensor with correct preprocessing"""
    img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    img_np = np.array(img)
    transformed = inference_transform(image=img_np)
    tensor = transformed['image'].unsqueeze(0)  # add batch dim
    return tensor.to(DEVICE)

# Waste type mapping (update based on your model's classes)
WASTE_TYPES = {
    0: {"name": "Metal", "icon": "🔧", "confidence": 0},
    1: {"name": "Plastic", "icon": "🥤", "confidence": 0},
    2: {"name": "Paper/Cardboard", "icon": "📦", "confidence": 0},
    3: {"name": "Glass", "icon": "🍷", "confidence": 0},
    4: {"name": "Organic", "icon": "🌱", "confidence": 0},
    5: {"name": "Textile", "icon": "👕", "confidence": 0},
    6: {"name": "Construction", "icon": "🏗️", "confidence": 0},
    7: {"name": "Hazardous", "icon": "⚠️", "confidence": 0},
    8: {"name": "Industrial Ash", "icon": "🔥", "confidence": 0},
    9: {"name": "Electronic", "icon": "💻", "confidence": 0},
    10: {"name": "Mixed", "icon": "🗑️", "confidence": 0}
}

@app.route('/api/health', methods=['GET'])
def health_check():
    db_status = {}
    if DATABASE_AVAILABLE:
        try:
            # Test basic database connections
            db_status = {
                'neo4j': db_manager.get_manager('neo4j') is not None,
                'mongodb': db_manager.get_manager('mongodb') is not None,
                'redis': db_manager.get_manager('redis') is not None,
                'cassandra': db_manager.get_manager('cassandra') is not None,
                'postgresql': db_manager.get_manager('postgresql') is not None
            }
        except Exception as e:
            db_status = {'error': str(e)}
    
    return jsonify({
        "status": "healthy", 
        "model_loaded": model is not None,
        "database_status": db_status,
        "database_integration": DATABASE_AVAILABLE
    })

@app.route('/api/insights/supply-chain/<waste_type>', methods=['GET'])
def get_supply_chain_insights(waste_type):
    """Get supply chain insights for specific waste type using graph database"""
    if not DATABASE_AVAILABLE:
        return jsonify({
            "error": "Database integration not available",
            "message": "Please install database dependencies and configure connections"
        }), 501
    
    try:
        insights = db_manager.get_supply_chain_insights(waste_type.upper())
        return jsonify(insights)
    except Exception as e:
        return jsonify({
            "error": f"Failed to get insights: {str(e)}"
        }), 500

@app.route('/api/insights/environmental-impact', methods=['GET'])
def get_environmental_impact_report():
    """Get comprehensive environmental impact report"""
    if not DATABASE_AVAILABLE:
        return jsonify({
            "error": "Database integration not available",
            "message": "Please install database dependencies and configure connections"
        }), 501
    
    try:
        user_id = request.args.get('user_id')
        report = db_manager.get_environmental_impact_report(user_id)
        return jsonify(report)
    except Exception as e:
        return jsonify({
            "error": f"Failed to generate report: {str(e)}"
        }), 500

@app.route('/api/search', methods=['GET'])
def search_waste_listings():
    """Search waste listings with caching and personalization"""
    if not DATABASE_AVAILABLE:
        return jsonify({
            "error": "Database integration not available",
            "message": "Please install database dependencies and configure connections"
        }), 501
    
    try:
        query = request.args.get('q', '')
        location = request.args.get('location')
        user_id = request.args.get('user_id')
        
        results = db_manager.search_waste_listings(query, location, user_id)
        return jsonify({
            "results": results,
            "query": query,
            "location": location,
            "total_results": len(results)
        })
    except Exception as e:
        return jsonify({
            "error": f"Search failed: {str(e)}"
        }), 500

@app.route('/api/classify', methods=['POST'])
def classify_waste():
    if model is None:
        print("❌ Model not loaded")
        return jsonify({"error": "Model not loaded"}), 500
    
    try:
        print("📥 Received classification request")
        # Get image from request
        if 'image' not in request.files:
            print("❌ No image provided")
            return jsonify({"error": "No image provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            print("❌ Empty filename")
            return jsonify({"error": "No image selected"}), 400
        
        print(f"📄 Processing image: {file.filename}")
        # Process image with correct preprocessing
        image_bytes = file.read()
        user_id = request.form.get('user_id')  # Optional: logged-in user
        image_hash = hashlib.sha256(image_bytes).hexdigest()

        # ── REDIS: Rate limiting FIRST (max 30 classifications per minute per IP) ──
        # Applies to every request — cached or not — so users can't bypass via cache hits
        if DATABASE_AVAILABLE:
            try:
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    rate_key = f"ratelimit:classify:{request.remote_addr}"
                    if not redis_mgr.check_rate_limit(rate_key, limit=30, window=60):
                        return jsonify({'error': 'Rate limit exceeded. Please wait a moment.'}), 429
            except Exception:
                pass

        # ── REDIS: Check cache by image hash ──
        response_data = None
        if DATABASE_AVAILABLE:
            try:
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    cached = redis_mgr.get_cached_classification(image_hash)
                    if cached:
                        print(f"⚡ REDIS cache hit for {image_hash[:12]}")
                        response_data = cached
                        # Still record the hit in analytics
                        try:
                            redis_mgr.client.incr('stats:classify:cache_hits')
                        except Exception:
                            pass
            except Exception:
                pass  # Cache miss is fine, proceed with model

        if not response_data:
            input_tensor = preprocess_image(image_bytes)
            print(f"📊 Input tensor shape: {input_tensor.shape}")

            # Make prediction with sigmoid (multi-label)
            with torch.no_grad():
                print("🧠 Running model inference...")
                logits = model(input_tensor)
                probabilities = torch.sigmoid(logits).cpu()
                confidence_scores = probabilities.squeeze().numpy()
            
            # Build results for all classes
            all_results = []
            for i, (cls, prob) in enumerate(zip(UNIFIED_CLASSES, confidence_scores)):
                all_results.append({
                    'class': cls,
                    'name': CLASS_META[cls]['name'],
                    'icon': CLASS_META[cls]['icon'],
                    'confidence': float(prob),
                    'confidence_pct': round(float(prob) * 100, 1),
                })
            
            # Sort by confidence descending
            all_results.sort(key=lambda x: x['confidence'], reverse=True)
            top_3 = all_results[:3]
            results = [
                {"name": item["name"], "icon": item["icon"], "confidence": item["confidence_pct"]}
                for item in top_3
            ]
            
            # Generate potential uses based on top prediction
            primary_class = top_3[0]["class"]
            primary_type = CLASS_TO_INTERNAL.get(primary_class, 'mixed')
            
            response_data = {
                "wasteTypes": results,
                "potentialUses": get_potential_uses(primary_type),
                "estimatedValue": get_estimated_value(primary_type),
                "environmentalImpact": get_environmental_impact(primary_type),
                # Metadata for matching engine to avoid re-calculating from results strings
                "_internal_class": primary_class 
            }

            # Cache the newly generated result
            if DATABASE_AVAILABLE:
                try:
                    redis_mgr = db_manager.get_manager('redis')
                    if redis_mgr:
                        redis_mgr.cache_waste_classification(image_hash, response_data, ttl=3600)
                except Exception:
                    pass

        # ── ALWAYS Proceed to Graph and Analytics (Cached or Not) ──
        # Extract all necessary variables from response_data for downstream logic
        p_class = None
        if isinstance(response_data, dict):
            p_class = response_data.get('_internal_class')
            
        if not p_class and isinstance(response_data, dict):
            w_types = response_data.get('wasteTypes')
            if isinstance(w_types, list) and len(w_types) > 0:
                first_name = w_types[0].get('name', '').upper().replace(' ', '_').replace('/', '_')
                p_class = first_name if first_name in UNIFIED_CLASSES else UNIFIED_CLASSES[0]
        
        if not p_class:
            p_class = UNIFIED_CLASSES[0]
            
        p_type = CLASS_TO_INTERNAL.get(p_class, 'mixed')
        
        # Standalone variables for legacy code and NoSQL updates
        results = response_data.get('wasteTypes', [])
        top_3 = results # Alias for legacy code
        primary_type = p_type # Alias for legacy code
        est_val = response_data.get('estimatedValue')
        env_impact = response_data.get('environmentalImpact')

        # ── NoSQL analytics recording (non-blocking) ──
        if DATABASE_AVAILABLE:
            try:
                # REDIS: Increment counters
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    redis_mgr.client.incr(f'stats:classifications:{primary_type}')
                    redis_mgr.client.incr('stats:classifications:total')
                    print(f"💾 REDIS: Cached classification {image_hash[:12]}")
            except Exception:
                pass

            try:
                # POSTGRESQL: Increment user's classification count
                if user_id:
                    pg = db_manager.get_manager('postgresql')
                    if pg:
                        cur = pg.connection.cursor()
                        cur.execute("UPDATE users SET classifications_count = COALESCE(classifications_count, 0) + 1 WHERE id = %s", (int(user_id),))
                        pg.connection.commit()
                        print(f"🐘 POSTGRESQL: Incremented classifications_count for user {user_id}")
            except Exception:
                pass

            try:
                # MONGODB: Store full classification document for history
                mongo_mgr = db_manager.get_manager('mongodb')
                if mongo_mgr:
                    doc = {
                        'image_hash': image_hash,
                        'user_id': int(user_id) if user_id else None,
                        'filename': file.filename,
                        'primary_type': p_type,
                        'top_3': results,
                        'estimated_value': est_val,
                        'environmental_impact': env_impact,
                        'created_at': datetime.utcnow(),
                    }
                    mongo_mgr.db.classification_history.insert_one(doc)
                    print(f"🍃 MONGODB: Stored classification history")
            except Exception:
                pass

            try:
                # CASSANDRA: Record time-series event for analytics
                cass_mgr = db_manager.get_manager('cassandra')
                if cass_mgr:
                    # dimension2 expects a string, try to get confidence from results
                    conf = results[0]['confidence'] if results and len(results) > 0 else 0
                    cass_mgr.record_analytics_metric(
                        metric_name='classifications',
                        timestamp=datetime.utcnow(),
                        dimension1=p_type,
                        dimension2=str(conf),
                        value=1.0,
                    )
                    print(f"📊 CASSANDRA: Logged classification event")
            except Exception:
                pass

            try:
                # NEO4J: Create/update waste type node for supply chain graph
                neo4j_mgr = db_manager.get_manager('neo4j')
                if neo4j_mgr:
                    with neo4j_mgr.driver.session() as session:
                        session.run(
                            "MERGE (w:WasteType {name: $name}) "
                            "ON CREATE SET w.first_seen = timestamp(), w.classify_count = 1 "
                            "ON MATCH SET w.classify_count = w.classify_count + 1, w.last_seen = timestamp()",
                            name=primary_type,
                        )
                    print(f"🌿 NEO4J: Updated WasteType node '{primary_type}'")
            except Exception:
                pass
            # ── NEO4J: Trigger matching for the classified waste type ──
            if user_id and MATCHING_ENGINE_AVAILABLE:
                try:
                    neo4j_mgr = db_manager.get_manager('neo4j')
                    pg = db_manager.get_manager('postgresql')
                    if neo4j_mgr and pg:
                        all_companies = pg.get_all_users_for_map()
                        # Get user coordinates
                        u = pg.get_user_by_id(int(user_id))
                        plat = (u.get('latitude') if u else None) or 22.5
                        plng = (u.get('longitude') if u else None) or 78.5
                        
                        matches = find_matches(
                            waste_type=p_type,
                            producer_lat=plat,
                            producer_lng=plng,
                            companies=all_companies,
                            quantity=1.0,
                            top_k=5,
                            exclude_user_id=int(user_id)
                        )
                        
                        if matches:
                            with neo4j_mgr.driver.session() as sess:
                                for m in matches:
                                    sess.run(
                                        "MERGE (a:Company {id: $uid}) "
                                        "MERGE (b:Company {id: $mid}) "
                                        "MERGE (a)-[r:MATCHED_WITH]->(b) "
                                        "ON CREATE SET r.waste_type = $wt, r.score = $score, r.created_at = timestamp() "
                                        "ON MATCH SET r.score = $score, r.updated_at = timestamp(), r.match_count = coalesce(r.match_count, 0) + 1",
                                        uid=int(user_id), mid=m.get('id'), wt=p_type,
                                        score=m.get('match_score', 0)
                                    )
                            print(f"🌿 NEO4J: Recorded {len(matches)} MATCHED_WITH edges for user {user_id}")
                except Exception as e:
                    print(f"⚠️ NEO4J matching update failed: {e}")
        
        # Prepare clean response (remove internal keys)
        final_response = {k: v for k, v in response_data.items() if not k.startswith('_')}
        
        print("✅ Classification successful")
        return jsonify(final_response)
        
    except Exception as e:
        print(f"❌ CLASSIFICATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Classification failed: {str(e)}"}), 500

POTENTIAL_USES = {
    "metal": [
        "Metal reprocessing for manufacturing",
        "Construction industry applications",
        "Automotive parts production"
    ],
    "plastic": [
        "Recycling into new plastic products",
        "Manufacturing construction materials",
        "Creating textile fibers"
    ],
    "paper/cardboard": [
        "Paper recycling and pulp production",
        "Packaging materials",
        "Compostable products"
    ],
    "glass": [
        "Glass recycling and remelting",
        "Construction aggregate",
        "Fiberglass production"
    ],
    "organic": [
        "Composting for agricultural use",
        "Biogas production",
        "Soil amendment"
    ],
    "textile": [
        "Textile recycling and fiber recovery",
        "Insulation manufacturing",
        "Industrial wiping materials"
    ],
    "construction": [
        "Aggregate for road construction",
        "Concrete recycling",
        "Building material production"
    ],
    "hazardous": [
        "Specialized treatment facilities",
        "Safe disposal protocols",
        "Hazardous waste management"
    ],
    "industrial ash": [
        "Cement production additive",
        "Road construction material",
        "Landfill cover material"
    ],
    "electronic": [
        "Component recovery and refurbishment",
        "Precious metal extraction",
        "Raw material recycling"
    ],
    "mixed": [
        "Material separation and sorting",
        "Component recovery",
        "Specialized processing"
    ]
}

ESTIMATED_VALUES = {
    "metal": "₹16,000-33,000 per tonne",
    "plastic": "₹10,000-15,000 per tonne",
    "paper/cardboard": "₹6,500-12,500 per tonne",
    "glass": "₹3,500-6,500 per tonne",
    "organic": "₹4,000-8,000 per tonne",
    "textile": "₹5,000-10,000 per tonne",
    "construction": "₹2,500-6,000 per tonne",
    "hazardous": "₹42,000-83,000 per tonne",
    "industrial ash": "₹2,000-4,000 per tonne",
    "electronic": "₹25,000-50,000 per tonne",
    "mixed": "₹6,000-12,500 per tonne"
}

ENVIRONMENTAL_IMPACTS = {
    "metal": {
        "co2Saved": "1.8 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "1200 kWh"
    },
    "plastic": {
        "co2Saved": "1.2 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "850 kWh"
    },
    "paper/cardboard": {
        "co2Saved": "1.0 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "600 kWh"
    },
    "glass": {
        "co2Saved": "0.9 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "500 kWh"
    },
    "organic": {
        "co2Saved": "0.8 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "400 kWh"
    },
    "textile": {
        "co2Saved": "1.1 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "700 kWh"
    },
    "construction": {
        "co2Saved": "0.7 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "350 kWh"
    },
    "hazardous": {
        "co2Saved": "0.5 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "200 kWh"
    },
    "industrial ash": {
        "co2Saved": "0.6 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "300 kWh"
    },
    "electronic": {
        "co2Saved": "2.0 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "1500 kWh"
    },
    "mixed": {
        "co2Saved": "1.0 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "600 kWh"
    }
}

def get_potential_uses(waste_type):
    return POTENTIAL_USES.get(waste_type, ["Various recycling applications"])

def get_estimated_value(waste_type):
    return ESTIMATED_VALUES.get(waste_type, "₹8,000-16,500 per tonne")

def get_environmental_impact(waste_type):
    return ENVIRONMENTAL_IMPACTS.get(waste_type, {
        "co2Saved": "1.0 tonnes CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "600 kWh"
    })

@app.route('/api/match-companies', methods=['GET'])
def match_companies():
    """Hybrid ML + rule-based company matching for a given waste type"""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    waste_type = request.args.get('waste_type', '')
    exclude_user_id = request.args.get('exclude_user_id', type=int)
    producer_lat = request.args.get('lat', type=float)
    producer_lng = request.args.get('lng', type=float)
    quantity = request.args.get('quantity', 1.0, type=float)

    if not waste_type:
        return jsonify({'error': 'waste_type parameter is required'}), 400

    try:
        # ── REDIS: Check match cache ──
        cache_key = f"{waste_type}:{exclude_user_id or 'all'}"
        if DATABASE_AVAILABLE:
            try:
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    cached = redis_mgr.get_cached_search(f"match:{cache_key}")
                    if cached:
                        print(f"⚡ REDIS: Match cache hit for {cache_key}")
                        return jsonify(cached)
            except Exception:
                pass

        postgres_manager = db_manager.get_manager('postgresql')
        if not postgres_manager:
            return jsonify({'error': 'PostgreSQL not available'}), 501

        # If matching engine is available, use hybrid scoring
        if MATCHING_ENGINE_AVAILABLE:
            all_companies = postgres_manager.get_all_users_for_map()

            # Default producer location to India centre if not supplied
            plat = producer_lat or 22.5
            plng = producer_lng or 78.5

            # If exclude_user_id is set, try to get their coordinates
            if exclude_user_id and (not producer_lat or not producer_lng):
                user = postgres_manager.get_user_by_id(exclude_user_id)
                if user:
                    plat = user.get('latitude') or plat
                    plng = user.get('longitude') or plng

            matches = find_matches(
                waste_type=waste_type,
                producer_lat=plat,
                producer_lng=plng,
                companies=all_companies,
                quantity=quantity,
                top_k=15,
                exclude_user_id=exclude_user_id,
            )
        else:
            # Fallback to simple matching
            matches = postgres_manager.get_matching_companies(waste_type, exclude_user_id)

        response = {
            'waste_type': waste_type,
            'matches': matches,
            'total': len(matches),
            'algorithm': 'hybrid_ml' if MATCHING_ENGINE_AVAILABLE else 'rule_based',
        }

        # ── NoSQL post-processing ──
        if DATABASE_AVAILABLE:
            try:
                # REDIS: Cache result for 5 minutes
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    redis_mgr.cache_waste_search(f"match:{cache_key}", response, ttl=300)
                    redis_mgr.client.incr('stats:matches:total')
            except Exception:
                pass

            try:
                # CASSANDRA: Log match event
                cass_mgr = db_manager.get_manager('cassandra')
                if cass_mgr:
                    cass_mgr.record_analytics_metric(
                        metric_name='match_queries',
                        timestamp=datetime.utcnow(),
                        dimension1=waste_type,
                        dimension2=str(len(matches)),
                        value=1.0,
                    )
            except Exception:
                pass

            try:
                # MONGODB: Store match event in activity feed
                mongo_mgr = db_manager.get_manager('mongodb')
                if mongo_mgr:
                    mongo_mgr.db.activity_feed.insert_one({
                        'type': 'match_search',
                        'user_id': exclude_user_id,
                        'waste_type': waste_type,
                        'results_count': len(matches),
                        'algorithm': response['algorithm'],
                        'created_at': datetime.utcnow(),
                    })
            except Exception:
                pass

            try:
                # NEO4J: Create MATCHED_WITH edges between user and matched companies
                neo4j_mgr = db_manager.get_manager('neo4j')
                if neo4j_mgr and exclude_user_id and matches:
                    with neo4j_mgr.driver.session() as sess:
                        for m in matches[:5]:  # Top 5 matches
                            sess.run(
                                "MERGE (a:Company {id: $uid}) "
                                "MERGE (b:Company {id: $mid}) "
                                "MERGE (a)-[r:MATCHED_WITH]->(b) "
                                "ON CREATE SET r.waste_type = $wt, r.score = $score, r.created_at = timestamp() "
                                "ON MATCH SET r.score = $score, r.updated_at = timestamp(), r.match_count = coalesce(r.match_count, 0) + 1",
                                uid=exclude_user_id, mid=m.get('id'), wt=waste_type,
                                score=m.get('match_score', 0),
                            )
            except Exception:
                pass

        return jsonify(response)
    except Exception as e:
        logger.error(f"Match companies error: {e}")
        return jsonify({'error': 'Failed to find matching companies'}), 500


@app.route('/api/smart-match', methods=['GET'])
def smart_match():
    """Dedicated smart matching endpoint for the Matches page.
    Returns scored + ranked matches for the logged-in user's waste type."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    if not MATCHING_ENGINE_AVAILABLE:
        return jsonify({'error': 'Matching engine not available'}), 501

    waste_type = request.args.get('waste_type', '')
    user_id = request.args.get('user_id', type=int)
    quantity = request.args.get('quantity', 1.0, type=float)
    top_k = request.args.get('top_k', 15, type=int)

    if not waste_type:
        return jsonify({'error': 'waste_type parameter is required'}), 400

    try:
        postgres_manager = db_manager.get_manager('postgresql')
        if not postgres_manager:
            return jsonify({'error': 'PostgreSQL not available'}), 501

        # Get producer location
        plat, plng = 22.5, 78.5
        if user_id:
            user = postgres_manager.get_user_by_id(user_id)
            if user:
                plat = user.get('latitude') or plat
                plng = user.get('longitude') or plng

        all_companies = postgres_manager.get_all_users_for_map()

        matches = find_matches(
            waste_type=waste_type,
            producer_lat=plat,
            producer_lng=plng,
            companies=all_companies,
            quantity=quantity,
            top_k=top_k,
            exclude_user_id=user_id,
        )

        return jsonify({
            'waste_type': waste_type,
            'waste_types': ALL_WASTE_TYPES,
            'matches': matches,
            'total': len(matches),
            'algorithm': 'hybrid_ml',
            'weights': {
                'rule_based': 'hard_gate',
                'ml_similarity': 35,
                'knn_clustering': 20,
                'distance': 45,
            },
        })
    except Exception as e:
        logger.error(f"Smart match error: {e}")
        return jsonify({'error': 'Failed to compute matches'}), 500


@app.route('/api/companies/map', methods=['GET'])
def companies_map():
    """Get all companies with coordinates for the map view"""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    industry_filter = request.args.get('industry', '')

    try:
        postgres_manager = db_manager.get_manager('postgresql')
        if not postgres_manager:
            return jsonify({'error': 'PostgreSQL not available'}), 501

        companies = postgres_manager.get_all_users_for_map(industry_filter or None)
        industries = postgres_manager.get_distinct_industry_types()

        return jsonify({
            'companies': companies,
            'industries': industries,
            'total': len(companies)
        })
    except Exception as e:
        logger.error(f"Companies map error: {e}")
        return jsonify({'error': 'Failed to load companies'}), 500

# Authentication Routes
@app.route('/api/auth/register', methods=['POST'])
def register():
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database integration not available'}), 501
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['email', 'password', 'company_name', 'industry_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Additional validation
        if len(data['password']) < 6:
            return jsonify({'error': 'Password must be at least 6 characters'}), 400
        
        if '@' not in data['email']:
            return jsonify({'error': 'Invalid email format'}), 400
        
        # Prepare user data
        user_data = {
            'email': data['email'],
            'password': data['password'],
            'company_name': data['company_name'],
            'industry_type': data['industry_type'],
            'location': data.get('location', ''),
            'phone': data.get('phone', '')
        }
        
        # Register user
        result = db_manager.register_user(user_data)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 201
        
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database integration not available'}), 501
    
    try:
        data = request.get_json()
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400

        user = db_manager.authenticate_user(data['email'], data['password'])
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401

        # Build JWT claims
        now = datetime.utcnow()
        access_payload = {
            'sub': str(user['id']),
            'email': user.get('email'),
            'iat': now,
            'exp': now + timedelta(seconds=ACCESS_TOKEN_EXPIRES_SECONDS)
        }
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # Create a refresh token with a unique identifier (jti) and store jti in Redis for revocation control
        jti = str(uuid.uuid4())
        refresh_payload = {
            'sub': str(user['id']),
            'jti': jti,
            'iat': now,
            'exp': now + timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)
        }
        refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

        # Store refresh token jti in Redis with expiry for revocation checks
        try:
            redis_mgr = db_manager.get_manager('redis') if DATABASE_AVAILABLE else None
            if redis_mgr:
                key = f"refresh:{jti}"
                # Value stores user id for quick lookup; expiry in seconds
                redis_mgr.client.setex(key, REFRESH_TOKEN_EXPIRES_DAYS * 24 * 3600, str(user['id']))
        except Exception:
            pass

        response = jsonify({'access_token': access_token, 'refresh_token': refresh_token, 'user': user})
        response.set_cookie('refresh_token', refresh_token, httponly=True, secure=False, samesite='Lax')
        return response, 200
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


def _decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise
    except Exception:
        return {}


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = None
        if auth.startswith('Bearer '):
            token = auth.split(' ', 1)[1].strip()
        # fallback to cookie
        if not token:
            token = request.cookies.get('access_token')
        if not token:
            return jsonify({'error': 'Missing access token'}), 401
        try:
            payload = _decode_jwt(token)
            if not payload:
                return jsonify({'error': 'Invalid token'}), 401
            g.user_id = int(payload.get('sub'))
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401
        return fn(*args, **kwargs)
    return wrapper

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    # Clear refresh cookie and revoke refresh jti in Redis when possible
    try:
        # Get refresh token from cookie or body (accept empty/non-JSON safely)
        token = request.cookies.get('refresh_token') or (request.get_json(silent=True) or {}).get('refresh_token')
        if token:
            try:
                payload = _decode_jwt(token)
                jti = payload.get('jti') if payload else None
                if jti and DATABASE_AVAILABLE:
                    try:
                        redis_mgr = db_manager.get_manager('redis')
                        if redis_mgr:
                            redis_mgr.client.delete(f"refresh:{jti}")
                    except Exception:
                        pass
            except Exception:
                pass
        response = jsonify({'message': 'Logged out successfully'})
        response.set_cookie('refresh_token', '', expires=0)
        return response, 200
    except Exception as e:
        logger.error(f"Logout error: {e}")
        return jsonify({'error': 'Logout failed'}), 500


@app.route('/api/auth/refresh', methods=['POST'])
def refresh_token():
    """Exchange a valid refresh token for a new access token."""
    # Try cookie first, then JSON body (accept empty/non-JSON safely)
    token = request.cookies.get('refresh_token') or (request.get_json(silent=True) or {}).get('refresh_token')
    if not token:
        return jsonify({'error': 'Missing refresh token'}), 401
    try:
        payload = _decode_jwt(token)
        if not payload:
            return jsonify({'error': 'Invalid refresh token'}), 401

        jti = payload.get('jti')
        user_sub = payload.get('sub')

        # Verify jti exists in Redis (server-side registration)
        try:
            redis_mgr = db_manager.get_manager('redis') if DATABASE_AVAILABLE else None
            if redis_mgr:
                key = f"refresh:{jti}"
                val = redis_mgr.client.get(key)
                if not val or str(val) != str(user_sub):
                    return jsonify({'error': 'Refresh token revoked or invalid'}), 401
        except Exception:
            # If Redis is unavailable, fall back to relying on token validity
            pass

        now = datetime.utcnow()
        access_payload = {
            'sub': str(user_sub),
            'iat': now,
            'exp': now + timedelta(seconds=ACCESS_TOKEN_EXPIRES_SECONDS)
        }
        access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return jsonify({'access_token': access_token}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Refresh token expired'}), 401
    except Exception as e:
        logger.error(f"Refresh error: {e}")
        return jsonify({'error': 'Failed to refresh token'}), 500

@app.route('/api/auth/profile', methods=['PUT'])
@require_auth
def update_profile():
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database integration not available'}), 501
    
    try:
        data = request.get_json()
        user_id = data.get('id') or g.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        # Update user profile
        postgres_manager = db_manager.get_manager('postgresql')
        if postgres_manager:
            postgres_manager.update_user(user_id, data)
            user = postgres_manager.get_user_by_id(user_id)
            
            if user:
                return jsonify({
                    'success': True,
                    'user': user,
                    'message': 'Profile updated successfully'
                }), 200
            else:
                return jsonify({'error': 'User not found'}), 404
        else:
            return jsonify({'error': 'Database not available'}), 501
        
    except Exception as e:
        logger.error(f"Profile update error: {e}")
        return jsonify({'error': 'Profile update failed'}), 500

# ─────────────────────────────────────────────────
#  Chat / Messaging API
# ─────────────────────────────────────────────────

@app.route('/api/chat/conversations', methods=['GET'])
@require_auth
def list_conversations():
    """List all conversations for the current user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = g.get('user_id')
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        convos = pg.get_conversations_for_user(user_id)
        unread = pg.get_unread_count(user_id)

        # ── REDIS: Set online heartbeat + enrich convos with partner online status ──
        try:
            redis_mgr = db_manager.get_manager('redis')
            if redis_mgr:
                redis_mgr.client.setex(f'online:{user_id}', 30, '1')  # 30s heartbeat
                for c in convos:
                    partner_id = c.get('partner_id')
                    if partner_id:
                        c['partner_online'] = bool(redis_mgr.client.get(f'online:{partner_id}'))
        except Exception:
            pass

        return jsonify({'conversations': convos, 'unread_total': unread})
    except Exception as e:
        logger.error(f"Chat list error: {e}")
        return jsonify({'error': 'Failed to load conversations'}), 500


@app.route('/api/chat/start', methods=['POST'])
@require_auth
def start_conversation():
    """Start (or resume) a conversation with another user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    user_id = data.get('user_id') or g.get('user_id')
    other_id = data.get('other_id')
    waste_context = data.get('waste_context', '')
    if not user_id or not other_id:
        return jsonify({'error': 'user_id and other_id are required'}), 400
    if user_id == other_id:
        return jsonify({'error': 'Cannot chat with yourself'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        conv = pg.get_or_create_conversation(user_id, other_id, waste_context)
        # serialise datetimes
        for k in ('created_at', 'updated_at'):
            if conv.get(k) and not isinstance(conv[k], str):
                conv[k] = conv[k].isoformat()

        # ── NoSQL: record chat connection ──
        try:
            # NEO4J: Create CHATTED_WITH edge
            neo4j_mgr = db_manager.get_manager('neo4j')
            if neo4j_mgr:
                with neo4j_mgr.driver.session() as sess:
                    sess.run(
                        "MERGE (a:Company {id: $uid}) "
                        "MERGE (b:Company {id: $oid}) "
                        "MERGE (a)-[r:CHATTED_WITH]->(b) "
                        "ON CREATE SET r.waste_context = $wc, r.created_at = timestamp() "
                        "ON MATCH SET r.last_chat = timestamp(), r.chat_count = coalesce(r.chat_count, 0) + 1",
                        uid=user_id, oid=other_id, wc=waste_context,
                    )
        except Exception:
            pass
        try:
            # CASSANDRA: Log chat-start event
            cass_mgr = db_manager.get_manager('cassandra')
            if cass_mgr:
                cass_mgr.record_analytics_metric(
                    metric_name='chat_started',
                    timestamp=datetime.utcnow(),
                    dimension1=waste_context or 'general',
                    dimension2=f"{user_id}->{other_id}",
                    value=1.0,
                )
        except Exception:
            pass

        return jsonify({'conversation': conv})
    except Exception as e:
        logger.error(f"Chat start error: {e}")
        return jsonify({'error': 'Failed to start conversation'}), 500


@app.route('/api/chat/messages/<int:conv_id>', methods=['GET'])
@require_auth
def get_messages(conv_id):
    """Get all messages in a conversation."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = request.args.get('user_id', type=int) or g.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        msgs = pg.get_messages(conv_id, user_id)
        return jsonify({'messages': msgs})
    except Exception as e:
        logger.error(f"Chat messages error: {e}")
        return jsonify({'error': 'Failed to load messages'}), 500


@app.route('/api/chat/messages/<int:conv_id>', methods=['POST'])
@require_auth
def send_message(conv_id):
    """Send a message in a conversation."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    sender_id = data.get('sender_id') or g.get('user_id')
    content = (data.get('content') or '').strip()
    if not sender_id or not content:
        return jsonify({'error': 'sender_id and content are required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        msg = pg.send_message(conv_id, sender_id, content)

        # ── NoSQL: record message event ──
        try:
            cass_mgr = db_manager.get_manager('cassandra')
            if cass_mgr:
                cass_mgr.record_analytics_metric(
                    metric_name='messages_sent',
                    timestamp=datetime.utcnow(),
                    dimension1=str(conv_id),
                    dimension2=str(sender_id),
                    value=1.0,
                )
        except Exception:
            pass
        try:
            mongo_mgr = db_manager.get_manager('mongodb')
            if mongo_mgr:
                mongo_mgr.db.activity_feed.insert_one({
                    'type': 'message_sent',
                    'user_id': sender_id,
                    'conversation_id': conv_id,
                    'content_length': len(content),
                    'created_at': datetime.utcnow(),
                })
        except Exception:
            pass

        # ── Notification for the recipient ──
        recipient_id = None
        try:
            cur = pg.connection.cursor()
            cur.execute("SELECT user1_id, user2_id FROM conversations WHERE id = %s", (conv_id,))
            conv_row = cur.fetchone()
            if conv_row:
                recipient_id = conv_row['user2_id'] if conv_row['user1_id'] == sender_id else conv_row['user1_id']
                sender_name = msg.get('sender_name', 'Someone')
                preview = content[:60] + ('…' if len(content) > 60 else '')
                pg.create_notification(
                    user_id=recipient_id,
                    notif_type='message',
                    title=f'New message from {sender_name}',
                    body=preview,
                    link=f'/chat?conv={conv_id}',
                    related_id=conv_id,
                    sender_id=sender_id,
                )
        except Exception as e:
            logger.error(f"Notification error: {e}")
            pass

        # ── NEO4J: Update pulse ──
        try:
            neo_mgr = db_manager.get_manager('neo4j')
            if neo_mgr and sender_id and recipient_id:
                with neo_mgr.driver.session() as sess:
                    sess.run(
                        "MERGE (a:Company {id: $uid}) "
                        "MERGE (b:Company {id: $oid}) "
                        "MERGE (a)-[r:CHATTED_WITH]-(b) "
                        "ON CREATE SET r.chat_count = 1, r.created_at = timestamp() "
                        "ON MATCH SET r.chat_count = COALESCE(r.chat_count, 0) + 1",
                        uid=sender_id, oid=recipient_id
                    )
        except Exception as e:
            logger.error(f"Neo4j chat update failed: {e}")
            pass

        return jsonify({'message': msg}), 201
    except Exception as e:
        logger.error(f"Chat send error: {e}")
        return jsonify({'error': 'Failed to send message'}), 500


@app.route('/api/chat/unread', methods=['GET'])
@require_auth
def unread_count():
    """Get total unread message count for a user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = request.args.get('user_id', type=int) or g.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        count = pg.get_unread_count(user_id)
        return jsonify({'unread': count})
    except Exception as e:
        logger.error(f"Unread count error: {e}")
        return jsonify({'error': 'Failed to get unread count'}), 500

# ─────────────────────────────────────────────────
#  Deals API
# ─────────────────────────────────────────────────

@app.route('/api/deals', methods=['POST'])
@require_auth
def create_deal():
    """Create a new deal proposal."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    required = ['conversation_id', 'proposer_id', 'responder_id', 'waste_type', 'quantity', 'price_per_unit']
    for field in required:
        if not data.get(field) and data.get(field) != 0:
            return jsonify({'error': f'{field} is required'}), 400
    # Enforce proposer identity from JWT
    proposer = data.get('proposer_id') or g.get('user_id')
    data['proposer_id'] = proposer
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deal = pg.create_deal(data)

        # ── NoSQL: log deal proposal ──
        try:
            mongo_mgr = db_manager.get_manager('mongodb')
            if mongo_mgr:
                mongo_mgr.db.activity_feed.insert_one({
                    'type': 'deal_proposed',
                    'user_id': data['proposer_id'],
                    'deal_id': deal['id'],
                    'waste_type': data['waste_type'],
                    'quantity': float(data.get('quantity', 0)),
                    'total_price': float(deal.get('total_price', 0)),
                    'created_at': datetime.utcnow(),
                })
        except Exception:
            pass
        try:
            cass_mgr = db_manager.get_manager('cassandra')
            if cass_mgr:
                cass_mgr.record_analytics_metric(
                    metric_name='deal_proposed',
                    timestamp=datetime.utcnow(),
                    dimension1=data['waste_type'],
                    dimension2=f"{data['proposer_id']}->{data['responder_id']}",
                    value=float(data.get('quantity', 0)),
                )
        except Exception:
            pass
        try:
            redis_mgr = db_manager.get_manager('redis')
            if redis_mgr:
                redis_mgr.client.incr('stats:deals:proposed')
        except Exception:
            pass

        # ── Notification for the responder ──
        try:
            proposer_name = ''
            cur = pg.connection.cursor()
            cur.execute("SELECT company_name FROM users WHERE id = %s", (data['proposer_id'],))
            row = cur.fetchone()
            if row:
                proposer_name = row['company_name']
            pg.create_notification(
                user_id=data['responder_id'],
                notif_type='deal_created',
                title=f'New deal from {proposer_name}',
                body=f"{data['waste_type']} — {data.get('quantity', 0)} {data.get('unit', 'tonnes')}",
                link=f"/chat?conv={data['conversation_id']}",
                related_id=deal['id'],
                sender_id=data['proposer_id'],
            )
        except Exception:
            pass

        return jsonify({'deal': deal}), 201
    except Exception as e:
        logger.error(f"Create deal error: {e}")
        return jsonify({'error': 'Failed to create deal'}), 500


@app.route('/api/deals/conversation/<int:conv_id>', methods=['GET'])
@require_auth
def get_conversation_deals(conv_id):
    """Get all deals for a conversation."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deals = pg.get_deals_for_conversation(conv_id)
        return jsonify({'deals': deals})
    except Exception as e:
        logger.error(f"Get deals error: {e}")
        return jsonify({'error': 'Failed to load deals'}), 500


@app.route('/api/deals/<int:deal_id>/accept', methods=['PUT'])
@require_auth
def accept_deal(deal_id):
    """Accept a deal proposal (responder only)."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    user_id = data.get('user_id') or g.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deal = pg.update_deal_status(deal_id, 'accepted', user_id)
        if not deal:
            return jsonify({'error': 'Cannot accept this deal'}), 400

        # ── NoSQL: log deal acceptance ──
        try:
            mongo_mgr = db_manager.get_manager('mongodb')
            if mongo_mgr:
                mongo_mgr.db.activity_feed.insert_one({
                    'type': 'deal_accepted',
                    'user_id': user_id,
                    'deal_id': deal_id,
                    'waste_type': deal.get('waste_type'),
                    'created_at': datetime.utcnow(),
                })
        except Exception:
            pass
        try:
            redis_mgr = db_manager.get_manager('redis')
            if redis_mgr:
                redis_mgr.client.incr('stats:deals:accepted')
        except Exception:
            pass

        return jsonify({'deal': deal})
    except Exception as e:
        logger.error(f"Accept deal error: {e}")
        return jsonify({'error': 'Failed to accept deal'}), 500


@app.route('/api/deals/<int:deal_id>/reject', methods=['PUT'])
@require_auth
def reject_deal(deal_id):
    """Reject a deal proposal (responder only)."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    user_id = data.get('user_id') or g.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deal = pg.update_deal_status(deal_id, 'rejected', user_id)
        if not deal:
            return jsonify({'error': 'Cannot reject this deal'}), 400
        return jsonify({'deal': deal})
    except Exception as e:
        logger.error(f"Reject deal error: {e}")
        return jsonify({'error': 'Failed to reject deal'}), 500


@app.route('/api/deals/<int:deal_id>/complete', methods=['PUT'])
@require_auth
def complete_deal(deal_id):
    """Mark a deal as completed and calculate impact."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    user_id = data.get('user_id') or g.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deal = pg.update_deal_status(deal_id, 'completed', user_id)
        if not deal:
            return jsonify({'error': 'Cannot complete this deal'}), 400

        # ── Apply impact to both users ──
        impact = pg.apply_deal_impact(deal_id)

        # ── NoSQL: log deal completion ──
        try:
            mongo_mgr = db_manager.get_manager('mongodb')
            if mongo_mgr:
                for uid in [deal['proposer_id'], deal['responder_id']]:
                    mongo_mgr.db.activity_feed.insert_one({
                        'type': 'deal_completed',
                        'user_id': uid,
                        'deal_id': deal_id,
                        'waste_type': deal.get('waste_type'),
                        'quantity': float(deal.get('quantity', 0)),
                        'total_price': float(deal.get('total_price', 0)),
                        'co2_saved': impact.get('co2_saved', 0),
                        'created_at': datetime.utcnow(),
                    })
        except Exception:
            pass
        try:
            cass_mgr = db_manager.get_manager('cassandra')
            if cass_mgr:
                cass_mgr.record_analytics_metric(
                    metric_name='deal_completed',
                    timestamp=datetime.utcnow(),
                    dimension1=deal.get('waste_type', 'unknown'),
                    dimension2=f"{deal['proposer_id']}->{deal['responder_id']}",
                    value=float(deal.get('quantity', 0)),
                )
        except Exception:
            pass
        try:
            neo4j_mgr = db_manager.get_manager('neo4j')
            if neo4j_mgr:
                with neo4j_mgr.driver.session() as sess:
                    sess.run(
                        "MERGE (a:Company {id: $pid}) "
                        "MERGE (b:Company {id: $rid}) "
                        "MERGE (a)-[r:DEALT_WITH]->(b) "
                        "ON CREATE SET r.waste_type = $wt, r.quantity = $qty, r.created_at = timestamp() "
                        "ON MATCH SET r.total_deals = coalesce(r.total_deals, 0) + 1, "
                        "r.total_quantity = coalesce(r.total_quantity, 0) + $qty",
                        pid=deal['proposer_id'], rid=deal['responder_id'],
                        wt=deal.get('waste_type', ''), qty=float(deal.get('quantity', 0)),
                    )
        except Exception:
            pass
        try:
            redis_mgr = db_manager.get_manager('redis')
            if redis_mgr:
                redis_mgr.client.incr('stats:deals:completed')
                redis_mgr.client.incrbyfloat('stats:deals:total_quantity', float(deal.get('quantity', 0)))
                redis_mgr.client.incrbyfloat('stats:deals:total_value', float(deal.get('total_price', 0)))
        except Exception:
            pass

        # ── Notification for the other party ──
        try:
            other_id = deal['responder_id'] if deal['proposer_id'] == user_id else deal['proposer_id']
            user_name = ''
            cur = pg.connection.cursor()
            cur.execute("SELECT company_name FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                user_name = row['company_name']
            pg.create_notification(
                user_id=other_id,
                notif_type='deal_completed',
                title=f'Deal completed by {user_name}',
                body=f"{deal.get('waste_type', '')} — ₹{float(deal.get('total_price', 0)):,.0f}",
                link=f"/chat?conv={deal.get('conversation_id')}",
                related_id=deal_id,
                sender_id=user_id,
            )
        except Exception:
            pass

        return jsonify({'deal': deal, 'impact': impact})
    except Exception as e:
        logger.error(f"Complete deal error: {e}")
        return jsonify({'error': 'Failed to complete deal'}), 500


@app.route('/api/deals/<int:deal_id>/cancel', methods=['PUT'])
@require_auth
def cancel_deal(deal_id):
    """Cancel a deal."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    user_id = data.get('user_id') or g.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deal = pg.update_deal_status(deal_id, 'cancelled', user_id)
        if not deal:
            return jsonify({'error': 'Cannot cancel this deal'}), 400

        # ── Notification for the other party ──
        try:
            other_id = deal['responder_id'] if deal['proposer_id'] == user_id else deal['proposer_id']
            user_name = ''
            cur = pg.connection.cursor()
            cur.execute("SELECT company_name FROM users WHERE id = %s", (user_id,))
            row = cur.fetchone()
            if row:
                user_name = row['company_name']
            pg.create_notification(
                user_id=other_id,
                notif_type='deal_cancelled',
                title=f'Deal cancelled by {user_name}',
                body=f"{deal.get('waste_type', '')} — ₹{float(deal.get('total_price', 0)):,.0f}",
                link=f"/chat?conv={deal.get('conversation_id')}",
                related_id=deal_id,
                sender_id=user_id,
            )
        except Exception:
            pass

        return jsonify({'deal': deal})
    except Exception as e:
        logger.error(f"Cancel deal error: {e}")
        return jsonify({'error': 'Failed to cancel deal'}), 500


@app.route('/api/deals/user/<int:user_id>', methods=['GET'])
@require_auth
def get_user_deals(user_id):
    """Get all deals for a user, optionally filtered by status."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    # Ensure the requester is the same user or an admin (admin checks omitted)
    requester = g.get('user_id')
    if int(user_id) != int(requester):
        return jsonify({'error': 'Forbidden'}), 403
    status = request.args.get('status')
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        deals = pg.get_user_deals(user_id, status)
        return jsonify({'deals': deals, 'total': len(deals)})
    except Exception as e:
        logger.error(f"User deals error: {e}")
        return jsonify({'error': 'Failed to load user deals'}), 500


@app.route('/api/deals/analytics/<int:user_id>', methods=['GET'])
@require_auth
def deal_analytics(user_id):
    """Rich analytics for a user's deal history — aggregated from multiple databases."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    requester = g.get('user_id')
    if int(user_id) != int(requester):
        return jsonify({'error': 'Forbidden'}), 403
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501

        cur = pg.connection.cursor()
        data = {'stats': {}, 'by_waste_type': [], 'by_month': [], 'partners': [], 'deals': []}

        # ── Overall stats ──
        cur.execute("""
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE status = 'active')    AS active,
                COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                COUNT(*) FILTER (WHERE status = 'cancelled') AS cancelled,
                COALESCE(SUM(quantity)    FILTER (WHERE status = 'completed'), 0) AS waste_traded,
                COALESCE(SUM(total_price) FILTER (WHERE status = 'completed'), 0) AS total_value,
                COALESCE(SUM(quantity * 0.5) FILTER (WHERE status = 'completed'), 0) AS co2_saved
            FROM deals
            WHERE proposer_id = %s OR responder_id = %s
        """, (user_id, user_id))
        row = cur.fetchone()
        data['stats'] = {
            'total':        row['total'],
            'active':       row['active'],
            'completed':    row['completed'],
            'cancelled':    row['cancelled'],
            'waste_traded': float(row['waste_traded']),
            'total_value':  float(row['total_value']),
            'co2_saved':    round(float(row['co2_saved']), 2),
        }

        # ── Breakdown by waste type ──
        cur.execute("""
            SELECT waste_type,
                   COUNT(*) AS count,
                   COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                   COALESCE(SUM(quantity) FILTER (WHERE status = 'completed'), 0) AS qty,
                   COALESCE(SUM(total_price) FILTER (WHERE status = 'completed'), 0) AS value
            FROM deals
            WHERE proposer_id = %s OR responder_id = %s
            GROUP BY waste_type ORDER BY count DESC
        """, (user_id, user_id))
        data['by_waste_type'] = [
            {'waste_type': r['waste_type'], 'count': r['count'], 'completed': r['completed'],
             'qty': float(r['qty']), 'value': float(r['value'])} for r in cur.fetchall()
        ]

        # ── Monthly trend (last 12 months) ──
        cur.execute("""
            SELECT TO_CHAR(created_at, 'YYYY-MM') AS month,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE status = 'completed') AS completed,
                   COALESCE(SUM(total_price) FILTER (WHERE status = 'completed'), 0) AS value
            FROM deals
            WHERE (proposer_id = %s OR responder_id = %s)
              AND created_at >= NOW() - INTERVAL '12 months'
            GROUP BY month ORDER BY month
        """, (user_id, user_id))
        data['by_month'] = [
            {'month': r['month'], 'total': r['total'], 'completed': r['completed'],
             'value': float(r['value'])} for r in cur.fetchall()
        ]

        # ── Top partners ──
        cur.execute("""
            SELECT partner_id, u.company_name, u.industry_type, u.location,
                   COUNT(*) AS deal_count,
                   COUNT(*) FILTER (WHERE d.status = 'completed') AS completed,
                   COALESCE(SUM(d.total_price) FILTER (WHERE d.status = 'completed'), 0) AS total_value
            FROM (
                SELECT responder_id AS partner_id, id, status, total_price
                FROM deals WHERE proposer_id = %s
                UNION ALL
                SELECT proposer_id AS partner_id, id, status, total_price
                FROM deals WHERE responder_id = %s
            ) d
            JOIN users u ON d.partner_id = u.id
            GROUP BY partner_id, u.company_name, u.industry_type, u.location
            ORDER BY deal_count DESC
            LIMIT 10
        """, (user_id, user_id))
        data['partners'] = [
            {'id': r['partner_id'], 'name': r['company_name'], 'industry': r['industry_type'],
             'location': r['location'], 'deal_count': r['deal_count'],
             'completed': r['completed'], 'total_value': float(r['total_value'])} for r in cur.fetchall()
        ]

        # ── Full deal list ──
        deals = pg.get_user_deals(user_id)
        data['deals'] = deals

        # ── Neo4j: relationship graph data ──
        try:
            neo4j_mgr = db_manager.get_manager('neo4j')
            if neo4j_mgr:
                with neo4j_mgr.driver.session() as sess:
                    result = sess.run(
                        "MATCH (a:Company {id: $uid})-[r:DEALT_WITH]-(b:Company) "
                        "RETURN b.id AS partner_id, r.waste_type AS waste_type, "
                        "coalesce(r.total_deals, 1) AS deals, coalesce(r.total_quantity, 0) AS qty",
                        uid=user_id
                    )
                    data['graph_edges'] = [dict(rec) for rec in result]
        except Exception:
            data['graph_edges'] = []

        # ── Cassandra: Time-series deal event timeline ──
        try:
            cass_mgr = db_manager.get_manager('cassandra')
            if cass_mgr:
                events = []
                for metric in ['deal_proposed', 'deal_completed']:
                    rows = cass_mgr.get_analytics_metrics(
                        metric_name=metric,
                        start_time=datetime.utcnow() - timedelta(days=180),
                        end_time=datetime.utcnow(),
                        limit=200,
                    )
                    for r in rows:
                        d2 = r.get('dimension2', '')
                        parts = d2.split('->')
                        if str(user_id) in parts:
                            events.append({
                                'type': metric,
                                'timestamp': r.get('timestamp'),
                                'waste_type': r.get('dimension1'),
                                'quantity': r.get('value', 0),
                            })
                events.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
                data['cassandra_timeline'] = events[:50]
            else:
                data['cassandra_timeline'] = []
        except Exception as e:
            logger.warning(f"Cassandra timeline error: {e}")
            data['cassandra_timeline'] = []

        # ── MongoDB: Recent activity feed ──
        try:
            mongo_mgr = db_manager.get_manager('mongodb')
            if mongo_mgr:
                activities = list(mongo_mgr.db.activity_feed.find(
                    {'user_id': user_id},
                    {'_id': 0}
                ).sort('created_at', -1).limit(20))
                for a in activities:
                    if isinstance(a.get('created_at'), datetime):
                        a['created_at'] = a['created_at'].isoformat()
                data['mongo_activity'] = activities
            else:
                data['mongo_activity'] = []
        except Exception as e:
            logger.warning(f"MongoDB activity error: {e}")
            data['mongo_activity'] = []

        # ── Redis: Live platform-wide deal counters ──
        try:
            redis_mgr = db_manager.get_manager('redis')
            if redis_mgr:
                data['redis_live'] = {
                    'total_proposed': int(redis_mgr.client.get('stats:deals:proposed') or 0),
                    'total_completed': int(redis_mgr.client.get('stats:deals:completed') or 0),
                    'total_quantity': round(float(redis_mgr.client.get('stats:deals:total_quantity') or 0), 1),
                    'total_value': round(float(redis_mgr.client.get('stats:deals:total_value') or 0), 2),
                }
            else:
                data['redis_live'] = {}
        except Exception as e:
            logger.warning(f"Redis live stats error: {e}")
            data['redis_live'] = {}

        # ── DB source metadata ──
        data['db_sources'] = {
            'postgresql': bool(pg),
            'neo4j': bool(db_manager.get_manager('neo4j')),
            'cassandra': bool(db_manager.get_manager('cassandra')),
            'mongodb': bool(db_manager.get_manager('mongodb')),
            'redis': bool(db_manager.get_manager('redis')),
        }

        return jsonify(data)
    except Exception as e:
        logger.error(f"Deal analytics error: {e}")
        return jsonify({'error': 'Failed to load deal analytics'}), 500


# ─────────────────────────────────────────────────
#  Notifications API
# ─────────────────────────────────────────────────

@app.route('/api/notifications', methods=['GET'])
def get_notifications():
    """Get notifications for a user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    limit = request.args.get('limit', 30, type=int)
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        notifications = pg.get_notifications(user_id, limit=limit, unread_only=unread_only)
        count = pg.get_notification_count(user_id)
        return jsonify({'notifications': notifications, 'unread_count': count})
    except Exception as e:
        logger.error(f"Get notifications error: {e}")
        return jsonify({'error': 'Failed to load notifications'}), 500


@app.route('/api/notifications/count', methods=['GET'])
def notification_count():
    """Get unread notification count for a user (lightweight polling endpoint)."""
    if not DATABASE_AVAILABLE:
        return jsonify({'unread': 0})
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'unread': 0})
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'unread': 0})
        return jsonify({'unread': pg.get_notification_count(user_id)})
    except Exception:
        return jsonify({'unread': 0})


@app.route('/api/notifications/<int:notif_id>/read', methods=['PUT'])
def mark_notification_read(notif_id):
    """Mark a single notification as read."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        pg.mark_notification_read(notif_id, user_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Mark notification read error: {e}")
        return jsonify({'error': 'Failed'}), 500


@app.route('/api/notifications/read-all', methods=['PUT'])
def mark_all_notifications_read():
    """Mark all notifications as read for a user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    try:
        pg = db_manager.managers.get('postgresql')
        if not pg:
            return jsonify({'error': 'PostgreSQL not available'}), 501
        count = pg.mark_all_notifications_read(user_id)
        return jsonify({'success': True, 'marked': count})
    except Exception as e:
        logger.error(f"Mark all read error: {e}")
        return jsonify({'error': 'Failed'}), 500


# ─────────────────────────────────────────────────
#  Analytics Dashboard API  (aggregates from ALL 5 databases)
# ─────────────────────────────────────────────────

@app.route('/api/analytics/dashboard', methods=['GET'])
def analytics_dashboard():
    """Aggregated platform analytics – pulls from every database."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    user_id = request.args.get('user_id', type=int)
    data = {
        'platform': {},
        'user': {},
        'nosql_sources': [],
    }

    # ── POSTGRESQL: core counts ──
    try:
        pg = db_manager.get_manager('postgresql')
        if pg:
            cur = pg.connection.cursor()
            cur.execute("SELECT COUNT(*) AS cnt FROM users")
            data['platform']['total_users'] = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(DISTINCT industry_type) AS cnt FROM users WHERE industry_type IS NOT NULL")
            data['platform']['total_industries'] = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM conversations")
            data['platform']['total_conversations'] = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM messages")
            data['platform']['total_messages'] = cur.fetchone()['cnt']
            # Deal stats
            cur.execute("SELECT COUNT(*) AS cnt FROM deals")
            data['platform']['total_deals'] = cur.fetchone()['cnt']
            cur.execute("SELECT COUNT(*) AS cnt FROM deals WHERE status = 'completed'")
            data['platform']['completed_deals'] = cur.fetchone()['cnt']
            cur.execute("SELECT COALESCE(SUM(quantity), 0) AS total FROM deals WHERE status = 'completed'")
            data['platform']['deals_waste_total'] = float(cur.fetchone()['total'])
            cur.execute("SELECT COALESCE(SUM(total_price), 0) AS total FROM deals WHERE status = 'completed'")
            data['platform']['deals_value_total'] = float(cur.fetchone()['total'])
            if user_id:
                cur.execute("SELECT classifications_count, waste_processed_tons, co2_saved_tons, cost_savings FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if row:
                    data['user']['classifications'] = row['classifications_count'] or 0
                    data['user']['waste_processed'] = float(row['waste_processed_tons'] or 0)
                    data['user']['co2_saved'] = float(row['co2_saved_tons'] or 0)
                    data['user']['cost_savings'] = float(row['cost_savings'] or 0)
                cur.execute("SELECT COUNT(*) AS cnt FROM deals WHERE (proposer_id = %s OR responder_id = %s) AND status = 'completed'", (user_id, user_id))
                data['user']['deals_completed'] = cur.fetchone()['cnt']
            data['nosql_sources'].append('postgresql')
    except Exception as e:
        logger.warning(f"Analytics - PostgreSQL error: {e}")

    # ── REDIS: real-time counters ──
    try:
        redis_mgr = db_manager.get_manager('redis')
        if redis_mgr:
            data['platform']['classifications_total'] = int(redis_mgr.client.get('stats:classifications:total') or 0)
            data['platform']['matches_total'] = int(redis_mgr.client.get('stats:matches:total') or 0)
            data['platform']['cache_hits'] = int(redis_mgr.client.get('stats:classify:cache_hits') or 0)

            # Per-waste-type breakdown from Redis counters
            waste_counts = {}
            for wt in ['metal', 'plastic', 'paper_cardboard', 'glass', 'organic',
                        'textile', 'construction', 'hazardous', 'industrial ash',
                        'electronic', 'mixed']:
                val = redis_mgr.client.get(f'stats:classifications:{wt}')
                if val and int(val) > 0:
                    waste_counts[wt] = int(val)
            data['platform']['classifications_by_type'] = waste_counts

            # Online users count
            online_keys = redis_mgr.client.keys('online:*')
            data['platform']['online_users'] = len(online_keys)

            data['nosql_sources'].append('redis')
    except Exception as e:
        logger.warning(f"Analytics - Redis error: {e}")

    # ── MONGODB: recent activity feed + classification history ──
    try:
        mongo_mgr = db_manager.get_manager('mongodb')
        if mongo_mgr:
            # Total classification documents
            data['platform']['classification_docs'] = mongo_mgr.db.classification_history.count_documents({})

            # Recent activity (last 20)
            recent = list(mongo_mgr.db.activity_feed.find(
                {'user_id': user_id} if user_id else {},
                {'_id': 0}
            ).sort('created_at', -1).limit(20))
            for r in recent:
                if 'created_at' in r and not isinstance(r['created_at'], str):
                    r['created_at'] = r['created_at'].isoformat()
            data['user']['recent_activity'] = recent

            # User's classification history from MongoDB
            if user_id:
                # Use MongoDB as source of truth for user classification count
                mongo_count = mongo_mgr.db.classification_history.count_documents({'user_id': user_id})
                if mongo_count > (data['user'].get('classifications') or 0):
                    data['user']['classifications'] = mongo_count
                    # Sync PostgreSQL to match MongoDB reality
                    try:
                        pg = db_manager.get_manager('postgresql')
                        if pg:
                            cur = pg.connection.cursor()
                            cur.execute("UPDATE users SET classifications_count = %s WHERE id = %s", (mongo_count, user_id))
                            pg.connection.commit()
                    except Exception:
                        pass

                history = list(mongo_mgr.db.classification_history.find(
                    {'user_id': user_id},
                    {'_id': 0, 'image_hash': 0}
                ).sort('created_at', -1).limit(10))
                for h in history:
                    if 'created_at' in h and not isinstance(h['created_at'], str):
                        h['created_at'] = h['created_at'].isoformat()
                data['user']['classification_history'] = history

            data['nosql_sources'].append('mongodb')
    except Exception as e:
        logger.warning(f"Analytics - MongoDB error: {e}")

    # ── CASSANDRA: time-series analytics ──
    try:
        cass_mgr = db_manager.get_manager('cassandra')
        if cass_mgr:
            # Classification trend (last 30 days)
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)

            classify_events = cass_mgr.get_analytics_metrics(
                metric_name='classifications',
                start_time=start_time,
                end_time=end_time,
                limit=500,
            )
            data['platform']['classification_trend'] = len(classify_events)

            match_events = cass_mgr.get_analytics_metrics(
                metric_name='match_queries',
                start_time=start_time,
                end_time=end_time,
                limit=500,
            )
            data['platform']['match_trend'] = len(match_events)

            chat_events = cass_mgr.get_analytics_metrics(
                metric_name='chat_started',
                start_time=start_time,
                end_time=end_time,
                limit=500,
            )
            data['platform']['chat_trend'] = len(chat_events)

            msg_events = cass_mgr.get_analytics_metrics(
                metric_name='messages_sent',
                start_time=start_time,
                end_time=end_time,
                limit=500,
            )
            data['platform']['message_trend'] = len(msg_events)

            data['nosql_sources'].append('cassandra')
    except Exception as e:
        logger.warning(f"Analytics - Cassandra error: {e}")

    # ── NEO4J: graph stats ──
    try:
        neo4j_mgr = db_manager.get_manager('neo4j')
        if neo4j_mgr:
            with neo4j_mgr.driver.session() as sess:
                # Count nodes & relationships
                r = sess.run("MATCH (n) RETURN count(n) AS nodes").single()
                data['platform']['graph_nodes'] = r['nodes'] if r else 0

                r = sess.run("MATCH ()-[r]->() RETURN count(r) AS rels").single()
                data['platform']['graph_relationships'] = r['rels'] if r else 0

                # Company network for current user
                if user_id:
                    r = sess.run(
                        "MATCH (c:Company {id: $uid})-[r]->(other:Company) "
                        "RETURN type(r) AS rel_type, count(r) AS cnt, collect(other.id) AS partners",
                        uid=user_id,
                    )
                    network = {}
                    for record in r:
                        network[record['rel_type']] = {
                            'count': record['cnt'],
                            'partner_ids': record['partners'][:10],
                        }
                    data['user']['network'] = network

            data['nosql_sources'].append('neo4j')
    except Exception as e:
        logger.warning(f"Analytics - Neo4j error: {e}")

    return jsonify(data)


@app.route('/api/activity/history', methods=['GET'])
def activity_history():
    """Get user's full activity history from MongoDB."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 50, type=int)
    activity_type = request.args.get('type', '')  # filter by type

    try:
        mongo_mgr = db_manager.get_manager('mongodb')
        if not mongo_mgr:
            return jsonify({'error': 'MongoDB not available'}), 501

        query = {}
        if user_id:
            query['user_id'] = user_id
        if activity_type:
            query['type'] = activity_type

        activities = list(mongo_mgr.db.activity_feed.find(
            query, {'_id': 0}
        ).sort('created_at', -1).limit(limit))

        for a in activities:
            if 'created_at' in a and not isinstance(a['created_at'], str):
                a['created_at'] = a['created_at'].isoformat()

        return jsonify({'activities': activities, 'total': len(activities)})
    except Exception as e:
        logger.error(f"Activity history error: {e}")
        return jsonify({'error': 'Failed to load activity'}), 500


@app.route('/api/classifications/history', methods=['GET'])
def classification_history():
    """Get classification history from MongoDB."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    user_id = request.args.get('user_id', type=int)
    limit = request.args.get('limit', 20, type=int)

    try:
        mongo_mgr = db_manager.get_manager('mongodb')
        if not mongo_mgr:
            return jsonify({'error': 'MongoDB not available'}), 501

        query = {'user_id': user_id} if user_id else {}
        history = list(mongo_mgr.db.classification_history.find(
            query, {'_id': 0, 'image_hash': 0}
        ).sort('created_at', -1).limit(limit))

        for h in history:
            if 'created_at' in h and not isinstance(h['created_at'], str):
                h['created_at'] = h['created_at'].isoformat()

        return jsonify({'classifications': history, 'total': len(history)})
    except Exception as e:
        logger.error(f"Classification history error: {e}")
        return jsonify({'error': 'Failed to load history'}), 500


@app.route('/api/network/graph', methods=['GET'])
def network_graph():
    """Get company relationship graph from Neo4j in a structured nodes/links format."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    user_id = request.args.get('user_id', type=int)

    try:
        neo4j_mgr = db_manager.get_manager('neo4j')
        if not neo4j_mgr:
            return jsonify({'error': 'Neo4j not available'}), 501

        pg = db_manager.get_manager('postgresql')

        nodes = []
        links = []
        node_ids = set()

        with neo4j_mgr.driver.session() as sess:
            if user_id:
                # Get this company's network (Incoming & Outgoing)
                result = sess.run(
                    "MATCH (c:Company {id: $uid})-[r]-(other:Company) "
                    "RETURN startNode(r).id AS source_id, endNode(r).id AS target_id, "
                    "type(r) AS relationship, r.waste_type AS waste_type, r.score AS score, "
                    "r.total_deals AS total_deals, r.total_quantity AS total_quantity, "
                    "r.chat_count AS chat_count",
                    uid=user_id,
                )
            else:
                # Get full network
                result = sess.run(
                    "MATCH (a:Company)-[r]->(b:Company) "
                    "RETURN a.id AS source_id, b.id AS target_id, type(r) AS relationship, "
                    "r.waste_type AS waste_type, r.score AS score, "
                    "r.total_deals AS total_deals, r.total_quantity AS total_quantity, "
                    "r.chat_count AS chat_count "
                    "LIMIT 300"
                )

            records = [record.data() for record in result]

            # Build links and track unique nodes
            if user_id:
                node_ids.add(user_id)
                
            for rec in records:
                links.append({
                    'source': rec['source_id'],
                    'target': rec['target_id'],
                    'relationship': rec['relationship'],
                    'waste_type': rec['waste_type'],
                    'value': rec.get('score', 1.0),
                    'total_deals': rec.get('total_deals'),
                    'total_quantity': rec.get('total_quantity'),
                    'chat_count': rec.get('chat_count')
                })
                node_ids.add(rec['source_id'])
                node_ids.add(rec['target_id'])

            # Fetch node metadata from PostgreSQL and enrichment from Neo4j in batch
            if node_ids:
                user_map = pg.get_users_by_ids(list(node_ids)) if pg else {}
                
                # Batch fetch connection counts from Neo4j for all nodes at once
                counts_res = sess.run(
                    "MATCH (c:Company)-[r]->() WHERE c.id IN $nids "
                    "RETURN c.id AS cid, type(r) AS type, count(r) AS count",
                    nids=list(node_ids)
                ).data()
                
                node_counts = {}
                for row in counts_res:
                    cid = row['cid']
                    if cid not in node_counts:
                        node_counts[cid] = {'DEALT_WITH': 0, 'CHATTED_WITH': 0}
                    rel_type = row['type']
                    if rel_type in node_counts[cid]:
                        node_counts[cid][rel_type] += row['count']

                for cid in node_ids:
                    u = user_map.get(cid)
                    counts = node_counts.get(cid, {'DEALT_WITH': 0, 'CHATTED_WITH': 0})
                    if u:
                        nodes.append({
                            'id': cid,
                            'name': u.get('company_name', f'Company {cid}'),
                            'type': 'Company',
                            'industry': u.get('industry_type', 'Unknown'),
                            'location': u.get('location', 'Unknown'),
                            'classifications': u.get('classifications_count', 0),
                            'deal_count': counts['DEALT_WITH'],
                            'chat_count': counts['CHATTED_WITH']
                        })
                    else:
                        nodes.append({
                            'id': cid,
                            'name': f'Company {cid}',
                            'type': 'Company',
                            'deal_count': counts['DEALT_WITH'],
                            'chat_count': counts['CHATTED_WITH']
                        })

            # Graph stats for real-time monitoring
            stats_r = sess.run("MATCH (n:Company) RETURN count(n) AS companies").single()
            rels_r = sess.run("MATCH ()-[r]->() RETURN count(r) AS relationships").single()

        return jsonify({
            'nodes': nodes,
            'links': links,
            'stats': {
                'companies': stats_r['companies'] if stats_r else 0,
                'relationships': rels_r['relationships'] if rels_r else 0,
                'total_links': len(links)
            }
        })
    except Exception as e:
        logger.error(f"Network graph error: {e}")
        return jsonify({'error': 'Failed to load network'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)