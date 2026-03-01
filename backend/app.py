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

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

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

        # ── REDIS: Check cache by image hash ──
        image_hash = hashlib.sha256(image_bytes).hexdigest()
        cache_hit = False
        if DATABASE_AVAILABLE:
            try:
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    cached = redis_mgr.get_cached_classification(image_hash)
                    if cached:
                        print(f"⚡ REDIS cache hit for {image_hash[:12]}")
                        cache_hit = True
                        # Still record the event in analytics
                        try:
                            redis_mgr.client.incr('stats:classify:cache_hits')
                        except Exception:
                            pass
                        return jsonify(cached)
            except Exception:
                pass  # Cache miss is fine, proceed with model

        input_tensor = preprocess_image(image_bytes)
        print(f"📊 Input tensor shape: {input_tensor.shape}")
        
        # ── REDIS: Rate limiting (max 30 classifications per minute per IP) ──
        if DATABASE_AVAILABLE:
            try:
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    rate_key = f"ratelimit:classify:{request.remote_addr}"
                    if not redis_mgr.check_rate_limit(rate_key, limit=30, window=60):
                        return jsonify({'error': 'Rate limit exceeded. Please wait a moment.'}), 429
            except Exception:
                pass

        # Make prediction with sigmoid (multi-label)
        with torch.no_grad():
            print("🧠 Running model inference...")
            logits = model(input_tensor)
            print(f"🔢 Logits shape: {logits.shape}")
            probabilities = torch.sigmoid(logits).cpu()  # ← sigmoid for multi-label
            confidence_scores = probabilities.squeeze().numpy()
            print(f"📈 Confidence scores: {confidence_scores}")
        
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
        print(f"📋 All results: {[(r['name'], r['confidence_pct']) for r in all_results]}")
        
        # Get top 3 predictions
        top_3 = all_results[:3]
        results = [
            {
                "name": item["name"],
                "icon": item["icon"],
                "confidence": item["confidence_pct"]
            }
            for item in top_3
        ]
        
        # Generate potential uses based on top prediction
        primary_type = top_3[0]["name"].lower()
        potential_uses = get_potential_uses(primary_type.replace("/", "_"))
        estimated_value = get_estimated_value(primary_type.replace("/", "_"))
        environmental_impact = get_environmental_impact(primary_type.replace("/", "_"))
        
        # Build response
        response_data = {
            "wasteTypes": results,
            "potentialUses": potential_uses,
            "estimatedValue": estimated_value,
            "environmentalImpact": environmental_impact
        }

        # ── NoSQL analytics recording (non-blocking) ──
        if DATABASE_AVAILABLE:
            try:
                # REDIS: Cache the result + increment counters
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    redis_mgr.cache_waste_classification(image_hash, response_data, ttl=3600)
                    redis_mgr.client.incr(f'stats:classifications:{primary_type}')
                    redis_mgr.client.incr('stats:classifications:total')
                    print(f"💾 REDIS: Cached classification {image_hash[:12]}")
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
                        'primary_type': primary_type,
                        'top_3': results,
                        'all_scores': {r['name']: r['confidence_pct'] for r in all_results},
                        'estimated_value': estimated_value,
                        'environmental_impact': environmental_impact,
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
                    cass_mgr.record_analytics_metric(
                        metric_name='classifications',
                        timestamp=datetime.utcnow(),
                        dimension1=primary_type,
                        dimension2=str(top_3[0]['confidence_pct']),
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
        
        print("✅ Classification successful")
        return jsonify(response_data)
        
    except Exception as e:
        print(f"❌ CLASSIFICATION ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Classification failed: {str(e)}"}), 500

def get_potential_uses(waste_type):
    uses = {
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
    return uses.get(waste_type, ["Various recycling applications"])

def get_estimated_value(waste_type):
    values = {
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
    return values.get(waste_type, "₹8,000-16,500 per tonne")

def get_environmental_impact(waste_type):
    impacts = {
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
    return impacts.get(waste_type, {
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
                'rule_based': 35,
                'ml_similarity': 30,
                'knn_clustering': 15,
                'distance': 20,
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
        
        # Validate required fields
        if not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        # Authenticate user
        result = db_manager.authenticate_user(data['email'], data['password'])
        
        if result.get('success'):
            # In a real application, you would generate a JWT token here
            # For now, we'll return the user data
            response_data = {
                'success': True,
                'user': result['user'],
                'message': 'Login successful'
            }
            return jsonify(response_data), 200
        else:
            return jsonify(result), 401
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    # In a real application, you would invalidate the JWT token here
    return jsonify({'message': 'Logged out successfully'}), 200

@app.route('/api/auth/profile', methods=['PUT'])
def update_profile():
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database integration not available'}), 501
    
    try:
        data = request.get_json()
        user_id = data.get('id')
        
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
def list_conversations():
    """List all conversations for the current user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = request.args.get('user_id', type=int)
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
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
def start_conversation():
    """Start (or resume) a conversation with another user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    user_id = data.get('user_id')
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
def get_messages(conv_id):
    """Get all messages in a conversation."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = request.args.get('user_id', type=int)
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
def send_message(conv_id):
    """Send a message in a conversation."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    data = request.get_json()
    sender_id = data.get('sender_id')
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

        return jsonify({'message': msg}), 201
    except Exception as e:
        logger.error(f"Chat send error: {e}")
        return jsonify({'error': 'Failed to send message'}), 500


@app.route('/api/chat/unread', methods=['GET'])
def unread_count():
    """Get total unread message count for a user."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501
    user_id = request.args.get('user_id', type=int)
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
            if user_id:
                cur.execute("SELECT classifications_count, listings_count, waste_processed_tons, co2_saved_tons, cost_savings FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if row:
                    data['user']['classifications'] = row['classifications_count'] or 0
                    data['user']['listings'] = row['listings_count'] or 0
                    data['user']['waste_processed'] = float(row['waste_processed_tons'] or 0)
                    data['user']['co2_saved'] = float(row['co2_saved_tons'] or 0)
                    data['user']['cost_savings'] = float(row['cost_savings'] or 0)
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
    """Get company relationship graph from Neo4j."""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    user_id = request.args.get('user_id', type=int)

    try:
        neo4j_mgr = db_manager.get_manager('neo4j')
        if not neo4j_mgr:
            return jsonify({'error': 'Neo4j not available'}), 501

        pg = db_manager.get_manager('postgresql')

        with neo4j_mgr.driver.session() as sess:
            if user_id:
                # Get this company's network
                result = sess.run(
                    "MATCH (c:Company {id: $uid})-[r]->(other:Company) "
                    "RETURN other.id AS partner_id, type(r) AS relationship, "
                    "r.waste_type AS waste_type, r.score AS score, "
                    "r.chat_count AS chat_count",
                    uid=user_id,
                )
            else:
                # Get full network
                result = sess.run(
                    "MATCH (a:Company)-[r]->(b:Company) "
                    "RETURN a.id AS from_id, b.id AS to_id, type(r) AS relationship, "
                    "r.waste_type AS waste_type, r.score AS score "
                    "LIMIT 200"
                )

            edges = [record.data() for record in result]

            # Enrich with company names from PostgreSQL
            if pg and edges:
                company_ids = set()
                for e in edges:
                    company_ids.add(e.get('partner_id') or e.get('from_id'))
                    if e.get('to_id'):
                        company_ids.add(e['to_id'])
                company_ids.discard(None)

                names = {}
                for cid in company_ids:
                    try:
                        u = pg.get_user_by_id(cid)
                        if u:
                            names[cid] = u.get('company_name', f'Company {cid}')
                    except Exception:
                        pass

                for e in edges:
                    pid = e.get('partner_id') or e.get('to_id')
                    e['partner_name'] = names.get(pid, f'Company {pid}')
                    if e.get('from_id'):
                        e['from_name'] = names.get(e['from_id'], f'Company {e["from_id"]}')

            # Graph stats
            stats_r = sess.run(
                "MATCH (n:Company) RETURN count(n) AS companies"
            ).single()
            rels_r = sess.run(
                "MATCH ()-[r]->() RETURN count(r) AS relationships"
            ).single()

        return jsonify({
            'edges': edges,
            'total_edges': len(edges),
            'graph_stats': {
                'companies': stats_r['companies'] if stats_r else 0,
                'relationships': rels_r['relationships'] if rels_r else 0,
            },
        })
    except Exception as e:
        logger.error(f"Network graph error: {e}")
        return jsonify({'error': 'Failed to load network'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)