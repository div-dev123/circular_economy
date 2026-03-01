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
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
        input_tensor = preprocess_image(image_bytes)
        print(f"📊 Input tensor shape: {input_tensor.shape}")
        
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

        # Lightweight analytics recording (non-blocking, won't spam logs)
        if DATABASE_AVAILABLE:
            try:
                redis_mgr = db_manager.get_manager('redis')
                if redis_mgr:
                    redis_mgr.client.incr(f'classifications:{primary_type}')
            except Exception:
                pass  # Analytics failure should never affect classification
        
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
        "metal": "$200-400 per ton",
        "plastic": "$120-180 per ton",
        "paper/cardboard": "$80-150 per ton",
        "glass": "$40-80 per ton",
        "organic": "$50-100 per ton",
        "textile": "$60-120 per ton",
        "construction": "$30-70 per ton",
        "hazardous": "$500-1000 per ton",
        "industrial ash": "$25-50 per ton",
        "electronic": "$300-600 per ton",
        "mixed": "$75-150 per ton"
    }
    return values.get(waste_type, "$100-200 per ton")

def get_environmental_impact(waste_type):
    impacts = {
        "metal": {
            "co2Saved": "1.8 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "1200 kWh"
        },
        "plastic": {
            "co2Saved": "1.2 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "850 kWh"
        },
        "paper/cardboard": {
            "co2Saved": "1.0 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "600 kWh"
        },
        "glass": {
            "co2Saved": "0.9 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "500 kWh"
        },
        "organic": {
            "co2Saved": "0.8 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "400 kWh"
        },
        "textile": {
            "co2Saved": "1.1 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "700 kWh"
        },
        "construction": {
            "co2Saved": "0.7 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "350 kWh"
        },
        "hazardous": {
            "co2Saved": "0.5 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "200 kWh"
        },
        "industrial ash": {
            "co2Saved": "0.6 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "300 kWh"
        },
        "electronic": {
            "co2Saved": "2.0 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "1500 kWh"
        },
        "mixed": {
            "co2Saved": "1.0 tons CO₂",
            "landfillDiverted": "100%",
            "energyRecovered": "600 kWh"
        }
    }
    return impacts.get(waste_type, {
        "co2Saved": "1.0 tons CO₂",
        "landfillDiverted": "100%",
        "energyRecovered": "600 kWh"
    })

@app.route('/api/match-companies', methods=['GET'])
def match_companies():
    """Find companies whose industry can process a given waste type"""
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'Database not available'}), 501

    waste_type = request.args.get('waste_type', '')
    exclude_user_id = request.args.get('exclude_user_id', type=int)

    if not waste_type:
        return jsonify({'error': 'waste_type parameter is required'}), 400

    try:
        postgres_manager = db_manager.get_manager('postgresql')
        if not postgres_manager:
            return jsonify({'error': 'PostgreSQL not available'}), 501

        matches = postgres_manager.get_matching_companies(waste_type, exclude_user_id)
        return jsonify({
            'waste_type': waste_type,
            'matches': matches,
            'total': len(matches)
        })
    except Exception as e:
        logger.error(f"Match companies error: {e}")
        return jsonify({'error': 'Failed to find matching companies'}), 500

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)