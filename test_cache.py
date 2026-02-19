"""
Test système de cache
"""
import asyncio
import time
import shutil
from pathlib import Path
from app.cache.frame_cache import FrameCache
from app.utils.image_comparison import ImageComparator


async def test_cache():
    """Test cache avec frames simulées"""
    print("=" * 60)
    print("📦 TEST CACHE FRAMES")
    print("=" * 60)
    
    # Cache de test (petit TTL)
    cache = FrameCache(max_size=3, ttl_seconds=10)
    
    # Image test
    test_img = Path("test_image.png")
    if not test_img.exists():
        print("❌ Crée test_image.png")
        return
    
    # Test 1 : Ajout frames
    print("\n1️⃣ Ajout de 3 frames...")
    
    for i in range(3):
        # Copie temporaire (simule nouvelle capture)
        temp_img = Path(f"temp_frame_{i}.png")
        shutil.copy(test_img, temp_img)
        
        frame = await cache.add_frame(temp_img, f"Description {i}")
        print(f"   ✅ Frame {i+1} ajoutée : {frame.frame_id}")
        await asyncio.sleep(0.5)
    
    # Test 2 : Stats
    print("\n2️⃣ Statistiques cache...")
    stats = await cache.get_stats()
    print(f"   Total frames : {stats['total_frames']}")
    print(f"   Avec description : {stats['frames_with_description']}")
    print(f"   Taille : {stats['total_size_mb']:.2f} MB")
    
    # Test 3 : Dernière frame
    print("\n3️⃣ Récupération dernière frame...")
    latest = await cache.get_latest_frame()
    if latest:
        print(f"   ✅ Dernière : {latest.description}")
        print(f"   Âge : {latest.age_seconds():.1f}s")
    
    # Test 4 : Éviction (ajout 4ème frame)
    print("\n4️⃣ Test éviction (max=3, ajout 4ème)...")
    temp_img = Path("temp_frame_3.png")
    shutil.copy(test_img, temp_img)
    await cache.add_frame(temp_img, "Description 3")
    print(f"   Cache size : {cache.size()} (devrait être 3)")
    
    # Test 5 : Détection changement
    print("\n5️⃣ Test détection changement...")
    new_img = Path("temp_frame_new.png")
    shutil.copy(test_img, new_img)
    
    should_process, diff = await cache.should_process_new_frame(new_img)
    print(f"   Différence : {diff}")
    print(f"   Traiter Gemini : {should_process}")
    
    new_img.unlink()
    
    # Test 6 : TTL expiration
    print("\n6️⃣ Test expiration TTL (attente 11s)...")
    print("   Attente...")
    await asyncio.sleep(11)
    
    await cache.cleanup_expired()
    print(f"   Cache size après cleanup : {cache.size()}")
    
    # Nettoyage
    await cache.clear()
    print("\n✅ Tests terminés")


if __name__ == "__main__":
    asyncio.run(test_cache())