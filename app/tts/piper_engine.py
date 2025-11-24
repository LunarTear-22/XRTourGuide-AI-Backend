import subprocess
import os
import sys
from app.tts.text_normalizer import TextNormalizer

class PiperEngine:
    def __init__(self):
        print("Inizializzazione Piper TTS...")
        
        # 1. Calcolo Percorsi Assoluti
        # Cartella corrente: .../XRTourGuide/app/tts
        base_dir = os.path.dirname(os.path.abspath(__file__)) 
        # Cartella Root: .../XRTourGuide
        project_root = os.path.dirname(os.path.dirname(base_dir)) 
        
        # 2. Percorso Modello (Piper)
        self.model_path = os.path.join(project_root, "models", "it_IT-paola-medium.onnx")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"ERRORE CRITICO: Modello non trovato in: {self.model_path}")

        # 3. Percorso FFmpeg (Conversione MP3)
        # Cerca in XRTourGuide/bin/ffmpeg.exe
        self.ffmpeg_path = os.path.join(project_root, "bin", "ffmpeg.exe")
        
        # Fallback: Se non c'è nella cartella bin, prova a usare quello di sistema
        if not os.path.exists(self.ffmpeg_path):
            print(f"ffmpeg.exe non trovato in {self.ffmpeg_path}. Userò quello di sistema (se installato).")
            self.ffmpeg_path = "ffmpeg"


        self.normalizer = TextNormalizer()

    def genera_audio(self, testo, output_filename):

        # --- NORMALIZZAZIONE ---
        # Il testo grezzo diventa "testo fonetico"
        testo_processato = self.normalizer.clean_text(testo)
        
        is_mp3 = output_filename.endswith(".mp3")
        wav_temp = output_filename.replace(".mp3", ".wav") if is_mp3 else output_filename
        
        comando_piper = [
            sys.executable, "-m", "piper",
            "--model", self.model_path,
            "--output_file", wav_temp,
            "--sentence_silence", "0.5"
        ]

        my_env = os.environ.copy()
        my_env["PYTHONUTF8"] = "1"
        my_env["PYTHONIOENCODING"] = "utf-8"

        try:
            # 1. Genera WAV
            subprocess.run(
                comando_piper, 
                input=testo_processato.encode('utf-8'),
                env=my_env,
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE
            )
            
            if not is_mp3:
                return os.path.exists(wav_temp)

            # 2. Converti in MP3
            if os.path.exists(wav_temp):
                comando_ffmpeg = [
                    self.ffmpeg_path,
                    "-i", wav_temp,
                    "-y",
                    "-b:a", "128k",
                    "-af", "adelay=200|200",
                    output_filename
                ]
                
                subprocess.run(
                    comando_ffmpeg,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    check=True
                )
                
                # --- PULIZIA DEL WAV INTERMEDIO ---
                # Cancelliamo il file wav pesante perché ora abbiamo l'mp3
                try:
                    os.remove(wav_temp)
                    print(f"File temporaneo rimosso: {wav_temp}")
                except Exception as e:
                    print(f"Non sono riuscito a cancellare il wav: {e}")
                
                return os.path.exists(output_filename)
            
            return False

        except subprocess.CalledProcessError as e:
            print(f"Errore Processo: {e.stderr.decode('utf-8', errors='ignore')}")
            return False
        except Exception as e:
            print(f"Errore Generico: {e}")
            return False

# --- TEST ---
if __name__ == "__main__":
    engine = PiperEngine()
    
    print("Testing generazione MP3...")
    if engine.genera_audio("Prova conversione mp3 con parametri json.", "test_finale.mp3"):
        print("MP3 Generato con successo!")
    else:
        print("Errore generazione.")