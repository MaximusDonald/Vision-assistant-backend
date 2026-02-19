"""
Test Gemini + Comparaison images
"""
import asyncio
from pathlib import Path
from app.gemini.client import GeminiClient
from app.utils.image_comparison import ImageComparator


def test_gemini_vision():
    """Test description image"""
    print("=" * 60)
    print("🤖 TEST GEMINI VISION")
    print("=" * 60)
    
    client = GeminiClient()
    
    image_path = Path("test_image.png")
    if not image_path.exists():
        print("❌ Crée test_image.png")
        return
    
    print(f"\n📷 Image : {image_path.name}")
    
    # Description
    description = client.describe_image(image_path)
    print(f"\n✅ Description Gemini :")
    print(f"   {description}")


def test_image_comparison():
    """Test comparaison images"""
    print("\n" + "=" * 60)
    print("🔍 TEST COMPARAISON IMAGES")
    print("=" * 60)
    
    img1 = Path("test_image.png")
    img2 = Path("test_image.png")  # Même image
    
    if not img1.exists():
        print("❌ Crée test_image.png")
        return
    
    # Test 1 : Même image
    print("\n1️⃣ Comparaison image identique...")
    is_diff, score = ImageComparator.is_significant_change(img1, img2)
    print(f"   Score différence : {score}")
    print(f"   Changement significatif : {is_diff}")
    print(f"   ✅ {'Envoi Gemini' if is_diff else 'SKIP (économie quota)'}")


def test_question():
    """Test question contextuelle"""
    print("\n" + "=" * 60)
    print("❓ TEST QUESTION CONTEXTUELLE")
    print("=" * 60)
    
    client = GeminiClient()
    
    image_path = Path("test_image.png")
    if not image_path.exists():
        print("❌ Crée test_image.png")
        return
    
    # Description initiale
    description = client.describe_image(image_path)
    print(f"\n📝 Description initiale : {description}")
    
    # Question
    question = "Qu'est-ce que tu vois au centre ?"
    answer = client.answer_question(image_path, question, description)
    
    print(f"\n❓ Question : {question}")
    print(f"✅ Réponse : {answer}")


if __name__ == "__main__":
    test_gemini_vision()
    test_image_comparison()
    test_question()