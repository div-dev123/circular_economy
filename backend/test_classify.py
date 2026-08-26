import requests
import os

# Minimal script to test classification and Neo4j update
BASE_URL = "http://localhost:5002"
TEST_IMAGE = "test_image.jpg" # Need a dummy image

def test_classify():
    # Create a dummy image if not exists
    if not os.path.exists(TEST_IMAGE):
        from PIL import Image
        img = Image.new('RGB', (224, 224), color = (73, 109, 137))
        img.save(TEST_IMAGE)
    
    with open(TEST_IMAGE, 'rb') as f:
        files = {'image': f}
        data = {'user_id': '31'} # ITC Food Processing
        print(f"Sending classification request for user 31...")
        response = requests.post(f"{BASE_URL}/api/classify", files=files, data=data)
        
    if response.status_code == 200:
        print("✅ Classification request successful!")
        print("Response:", response.json())
    else:
        print(f"❌ Classification request failed with status {response.status_code}")
        print("Error:", response.text)

if __name__ == "__main__":
    test_classify()
