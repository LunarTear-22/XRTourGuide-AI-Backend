import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
bin_path = os.path.join(project_root, "bin")

# Controlliamo se esiste davvero
if os.path.exists(os.path.join(bin_path, "ffmpeg.exe")):
    print(f"Configurazione FFmpeg locale da: {bin_path}")
    # Aggiungiamo la cartella bin alla variabile d'ambiente PATH
    os.environ["PATH"] += os.pathsep + bin_path
else:
    print("ATTENZIONE: Non trovo ffmpeg.exe nella cartella 'bin' del progetto!")
# ---------------------------------------

import torch
import soundfile as sf
from f5_tts.api import F5TTS

# --- CONFIGURAZIONE ---
REF_TEXT = "Ora sì. Ma perchè quando? Non ho capito per quale motivo quando...  si aggiorna OBS mi leva il microfono." \
" Non ho capito ancora questo fatto.." 
GEN_TEXT = "Il Colosseo è un anfiteatro romano del primo secolo. La sua grandezza lascia senza fiato."

def run_f5_test():
    print("Inizializzazione F5-TTS...")

    # Controllo GPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"   Hardware rilevato: {device.upper()}")
    
    if device == "cpu":
        print("ATTENZIONE: Sto usando la CPU!")

    try:
        f5tts = F5TTS(device=device)
    except Exception as e:
        # Fallback nel caso l'API sia cambiata ancora
        print(f"Errore init standard: {e}. Provo parametri alternativi...")
        f5tts = F5TTS()

    # Percorsi file
    ref_audio_path = os.path.join(current_dir, "ref_voice.wav")
    output_path = os.path.join(current_dir, "f5_output.wav")

    if not os.path.exists(ref_audio_path):
        print(f"ERRORE: Manca il file audio di riferimento! Metti 'ref_voice.wav' in: {current_dir}")
        return

    print(f"Clonazione voce da: {os.path.basename(ref_audio_path)}")
    print("Generazione in corso (Attendi...)...")

    # INFERENZA
    try:
        wav, sr, _ = f5tts.infer(
            ref_file=ref_audio_path,
            ref_text=REF_TEXT,
            gen_text=GEN_TEXT
        )

        # Salvataggio
        sf.write(output_path, wav, sr)
        print(f"FATTO! Audio salvato in: {output_path}")
        
    except Exception as e:
        print(f"Errore durante la generazione: {e}")
        if "ffmpeg" in str(e).lower():
            print("Suggerimento: Sembra ancora un problema di FFmpeg. Controlla che ffmpeg.exe sia in XRTourGuide-AI-Backend/bin")

if __name__ == "__main__":
    run_f5_test()