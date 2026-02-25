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

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

def load_model():
    try:
        # Load checkpoint
        checkpoint = torch.load('model.pth', map_location=DEVICE)
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
    return jsonify({"status": "healthy", "model_loaded": model is not None})

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
        
        response_data = {
            "wasteTypes": results,
            "potentialUses": potential_uses,
            "estimatedValue": estimated_value,
            "environmentalImpact": environmental_impact
        }
        
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)