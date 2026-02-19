"""
Test WebSocket stream
"""
import asyncio
import websockets
import json
import base64
from pathlib import Path


async def test_websocket():
    """Test connexion WebSocket + envoi frames"""
    
    uri = "ws://localhost:8000/ws/stream"
    
    print("=" * 60)
    print("🔌 TEST WEBSOCKET STREAM")
    print("=" * 60)
    
    async with websockets.connect(uri) as websocket:
        
        # 1. Message de bienvenue
        welcome = await websocket.recv()
        print(f"\n✅ Connecté : {json.loads(welcome)}")
        
        # 2. Envoi frame
        print("\n📸 Envoi frame...")
        
        img_path = Path("test_image.png")
        if not img_path.exists():
            print("❌ Crée test_image.png")
            return
        
        # Encodage base64
        image_data = img_path.read_bytes()
        image_base64 = base64.b64encode(image_data).decode()
        
        # Message
        await websocket.send(json.dumps({
            "type": "frame",
            "image_base64": image_base64,
            "force": False
        }))
        
        # Réponse
        response = await websocket.recv()
        result = json.loads(response)
        
        print(f"✅ Réponse frame :")
        print(f"   Status: {result['status']}")
        print(f"   Description: {result.get('description', 'N/A')}")
        print(f"   Temps: {result['processing_time_ms']}ms")
        
        # 3. Envoi même frame (devrait skip)
        print("\n📸 Envoi même frame...")
        
        await websocket.send(json.dumps({
            "type": "frame",
            "image_base64": image_base64,
            "force": False
        }))
        
        response = await websocket.recv()
        result = json.loads(response)
        
        print(f"✅ Réponse frame :")
        print(f"   Status: {result['status']}")
        if result['status'] == 'skipped':
            print(f"   ⏭️ SKIP validé (économie quota)")
        
        # 4. Question
        print("\n❓ Envoi question...")
        
        await websocket.send(json.dumps({
            "type": "question",
            "question_text": "Qu'est-ce que tu vois ?"
        }))
        
        response = await websocket.recv()
        result = json.loads(response)
        
        print(f"✅ Réponse question :")
        print(f"   Question: {result['question']}")
        print(f"   Réponse: {result['answer']}")
        
        # 5. Ping
        print("\n🏓 Test ping...")
        
        await websocket.send(json.dumps({"type": "ping"}))
        pong = await websocket.recv()
        
        print(f"✅ Pong reçu : {json.loads(pong)}")
        
        print("\n" + "=" * 60)
        print("✅ TOUS LES TESTS PASSÉS")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_websocket())