"""
Test rapide de la couche voix
"""
import asyncio
from pathlib import Path
from app.models.whisper_loader import get_whisper_model
from app.voice.speech_to_text import SpeechToText
from app.voice.text_to_speech import TextToSpeech
from app.voice.audio_processor import AudioProcessor


async def test_tts():
    """Test Text-to-Speech"""
    print("=" * 60)
    print("🔊 TEST TEXT-TO-SPEECH")
    print("=" * 60)
    
    tts = TextToSpeech()
    
    # Textes de test
    texts = [
        "Bonjour, je suis votre assistant vocal.",
        "Personne devant vous, à trois mètres.",
        "Panneau sortie à droite.",
    ]
    
    for i, text in enumerate(texts, 1):
        print(f"\n{i}. Synthèse: \"{text}\"")
        
        audio_bytes = await tts.synthesize(text, language="fr", gender="female")
        
        # Sauvegarde pour écoute
        output_path = Path(f"test_tts_{i}.mp3")
        output_path.write_bytes(audio_bytes)
        
        print(f"   ✅ Audio sauvegardé: {output_path.name} ({len(audio_bytes)} bytes)")
    
    print("\n🎵 Écoute les fichiers test_tts_*.mp3 pour vérifier")


async def test_stt():
    """Test Speech-to-Text"""
    print("\n" + "=" * 60)
    print("🎤 TEST SPEECH-TO-TEXT")
    print("=" * 60)
    
    # Vérifie si fichier audio test existe
    test_audio = Path("test_audio.wav")
    
    if not test_audio.exists():
        print(f"\n⚠️ Pour tester STT, crée un fichier 'test_audio.wav' avec:")
        print("   - Une phrase en français")
        print("   - Format: WAV ou MP3")
        print("   - Durée: < 10 secondes")
        return
    
    # Chargement modèles
    print("\n🚀 Chargement Whisper...")
    model = get_whisper_model()
    
    
    # Transcription
    stt = SpeechToText(model)
    
    print(f"\n📝 Transcription: {test_audio.name}")
    text = stt.transcribe(test_audio, language="fr")
    
    print(f"\n✅ Résultat: \"{text}\"")


async def test_voices():
    """Liste les voix disponibles"""
    print("\n" + "=" * 60)
    print("🎙️ VOIX DISPONIBLES")
    print("=" * 60)
    
    tts = TextToSpeech()
    
    print("\n🇫🇷 Français:")
    for voice in tts.VOICES["fr"].values():
        print(f"   - {voice}")
    
    print("\n🇬🇧 Anglais:")
    for voice in tts.VOICES["en"].values():
        print(f"   - {voice}")


async def main():
    """Exécute tous les tests"""
    
    # Test 1 : TTS (ne nécessite pas de fichier)
    await test_tts()
    
    # Test 2 : STT (nécessite test_audio.wav)
    await test_stt()
    
    # Test 3 : Liste voix
    await test_voices()
    
    print("\n" + "=" * 60)
    print("✅ TESTS TERMINÉS")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())