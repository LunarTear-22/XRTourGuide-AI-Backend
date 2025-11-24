from TTS.api import TTS # type: ignore

model_name = "tts_models/it/mai_female/vits" 

print(f"Caricamento modello: {model_name}...")
tts = TTS(model_name=model_name)

tts.tts_to_file(
    text="Benvenuti nel tour virtuale. Senti come questa voce è meno metallica e più naturale.",
    file_path="test_vits.wav"
)

print("Audio generato: test_vits.wav")