import os
import torch
import torchaudio
import torchaudio.transforms as T
from TTS.api import TTS
from TTS.tts.configs.xtts_config import XttsConfig
from TTS.tts.models.xtts import Xtts

# --- CONFIGURAZIONE ---
TEXT = "Immaginatevi un gigantesco teatro, con gradinate che sembrano salire verso il cielo. " \
    "Il Colosseo, costruito nel primo secolo d.C., era il cuore del divertimento e della spettacolarità romana"
REF_AUDIO = "ref_voice.mp3" 

# --- PARAMETRI DI CORREZIONE ---
GEN_SPEED = 1.1       
PITCH_STEPS = -0.5       

def load_model_direct():
    print("Ricerca modello XTTS v2...")
    app_data = os.getenv('LOCALAPPDATA')
    model_path = os.path.join(app_data, "tts", "tts_models--multilingual--multi-dataset--xtts_v2")
    
    if not os.path.exists(model_path):
        temp = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    
    config = XttsConfig()
    config.load_json(os.path.join(model_path, "config.json"))
    model = Xtts.init_from_config(config)
    model.load_checkpoint(config, checkpoint_dir=model_path, eval=True)
    if torch.cuda.is_available(): model.cuda()
    return model, config

def run_direct_inference():
    model, config = load_model_direct()
    if model is None: return
    
    with torch.no_grad():
        print(f"Generazione (Speed: {GEN_SPEED} | Pitch Correction: {PITCH_STEPS})...")
        
        outputs = model.synthesize(
            TEXT,
            config,
            speaker_wav=REF_AUDIO,
            language="it",
            gpt_cond_len=6,
            speed=GEN_SPEED,
            temperature=0.2,
            do_sample=True,
            enable_text_splitting=False,
            repetition_penalty=5.0,
            top_k=60,
            top_p=0.8,
        )

        # --- POST PROCESSING ---
        print("Applicazione Deep Voice Fix...")
        wav_tensor = torch.tensor(outputs["wav"]).unsqueeze(0)

        # 1. PITCH SHIFTING
        if PITCH_STEPS != 0:
            pitch_shifter = T.PitchShift(sample_rate=24000, n_steps=PITCH_STEPS)
            wav_tensor = pitch_shifter(wav_tensor)

        # 2. Normalizzazione
        max_val = torch.abs(wav_tensor).max()
        if max_val > 0:
            wav_tensor = wav_tensor / max_val * 0.95

        # 3. Upsampling
        resampler = T.Resample(orig_freq=24000, new_freq=44100, dtype=torch.float32)
        wav_hq = resampler(wav_tensor)

        # --- SALVATAGGIO ---
        output_path = "xtts_deep_corrected.wav"
        
        # FIX FINALE: .detach().cpu() assicura che il tensore sia "morto" e pronto per il salvataggio
        torchaudio.save(output_path, wav_hq.detach().cpu(), 44100, bits_per_sample=32)
        
        print(f"FATTO! Audio salvato in: {output_path}")
        
        # Avviso sulla lunghezza
        if len(TEXT) > 200:
            print(" NOTA: Hai ricevuto un warning sulla lunghezza (213 caratteri).")
            print(" L'audio potrebbe essere tagliato alla fine. Ricorda di usare frasi corte nel backend finale!")

if __name__ == "__main__":
    run_direct_inference()