"""
Test complet API Gemini
"""
import requests
from pathlib import Path
import time


API_URL = "http://localhost:8000/api/v1"


def test_complete_workflow():
    """Test workflow complet"""
    
    print("=" * 60)
    print("🧪 TEST API COMPLETE - GEMINI EDITION")
    print("=" * 60)
    
    # Test 1 : Health check
    print("\n1️⃣ Health check...")
    r = requests.get(f"{API_URL}/health")
    print(f"   Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Modèle: {data['gemini_model']}")
        print(f"   📦 Cache: {data['cache']['total_frames']} frames")
    
    # Test 2 : Process première frame
    print("\n2️⃣ Traitement première frame...")
    
    img_path = Path("test_image.png")
    if not img_path.exists():
        print("   ❌ Crée test_image.png")
        return
    
    with open(img_path, "rb") as f:
        files = {"image": f}
        data = {"force": False}
        
        r = requests.post(f"{API_URL}/process-frame", files=files, data=data)
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ Status: {result['status']}")
        print(f"   📝 Description: {result['description']}")
        print(f"   ⏱️ Temps: {result['processing_time_ms']}ms")
        print(f"   🔍 Différence: {result['difference_score']}")
    else:
        print(f"   ❌ Erreur: {r.text}")
        return
    
    
    # Test 3 : Process même frame (devrait skip)
    print("\n3️⃣ Traitement même frame (devrait SKIP)...")
    time.sleep(1)
    
    with open(img_path, "rb") as f:
        files = {"image": f}
        data = {"force": False}
        
        r = requests.post(f"{API_URL}/process-frame", files=files, data=data)
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ✅ Status: {result['status']}")
        if result['status'] == 'skipped':
            print(f"   ⏭️ Raison: {result['reason']}")
            print(f"   🔍 Différence: {result['difference_score']} (seuil: {result['threshold']})")
            print(f"   ✅ ÉCONOMIE QUOTA VALIDÉE")
    
    
    # Test 4 : Question textuelle
    print("\n4️⃣ Question textuelle...")
    
    data = {"question_text": "Qu'est-ce que tu vois au centre ?"}
    r = requests.post(f"{API_URL}/ask", data=data)
    
    if r.status_code == 200:
        result = r.json()
        print(f"   ❓ Question: {result['question']}")
        print(f"   ✅ Réponse: {result['answer']}")
        print(f"   ⏱️ Temps: {result['processing_time_ms']}ms")
    else:
        print(f"   ❌ Erreur: {r.text}")
    
    # Test 5 : Scène actuelle
    print("\n5️⃣ Récupération scène actuelle...")
    
    r = requests.get(f"{API_URL}/current-scene")
    if r.status_code == 200:
        data = r.json()
        print(f"   ✅ Description: {data['description']}")
    
    # Test 6 : Stats cache
    print("\n6️⃣ Statistiques cache...")
    
    r = requests.get(f"{API_URL}/cache/stats")
    if r.status_code == 200:
        stats = r.json()
        print(f"   📦 Frames: {stats['total_frames']}/{stats['max_size']}")
        print(f"   📝 Avec description: {stats['frames_with_description']}")
        print(f"   💾 Taille: {stats['total_size_mb']:.2f} MB")
    
    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    test_complete_workflow()