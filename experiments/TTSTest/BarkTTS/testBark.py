import torch
from transformers import AutoProcessor, AutoModel
import scipy.io.wavfile as wavfile

# Carichi il processor e il modello
processor = AutoProcessor.from_pretrained("suno/bark")
model = AutoModel.from_pretrained("suno/bark")

# Testo da convertire in audio
texts = [
    "Ciao, questo è un esempio di Bark in modalità avanzata.",
]

# Processo il testo
inputs = processor(text=texts, return_tensors="pt")

# Generi il parlato
speech_values = model.generate(**inputs, do_sample=True)

# Estraggo l’array audio
audio = speech_values.cpu().numpy().squeeze()

# Sample rate del modello
sr = model.generation_config.sample_rate

# Salvo il file WAV
wavfile.write("bark_lowlevel.wav", sr, audio)