import soundfile as sf
from kokoro_onnx import Kokoro
import os
import io

class TTSEngine:
    def __init__(self):
        print("Inizializzazione Motore Kokoro (Voce: inglese)...")
        # Assicurati che questi file v1.0 siano nella cartella
        self.model_path = "kokoro-v1.0.onnx"
        self.voices_path = "voices-v1.0.bin"
        
        if not os.path.exists(self.model_path):
            raise FileNotFoundError("Manca kokoro-v1.0.onnx!")
            
        self.kokoro = Kokoro(self.model_path, self.voices_path)
        print("Motore TTS Pronto.")

    def genera_audio(self, testo, output_filename):
        print(f"Generazione: '{testo[:30]}...'")
        try:
            samples, sample_rate = self.kokoro.create(
                testo, 
                voice="if_sara", 
                speed=1, 
                lang="it"
            )

            # Salvataggio
            sf.write(output_filename, samples, sample_rate)
            print(f"File creato: {output_filename}")
            return True
            
        except Exception as e:
            print(f"Errore TTS: {e}")
            return False

# --- BLOCCO DI TEST ---
if __name__ == "__main__":
    # Simuliamo l'uso nel backend
    motore = TTSEngine()
    
    descrizione = "Immaginatevi un gigantesco teatro, con gradinate che sembrano salire verso il cielo... " \
    "Il Colosseo! Costruito nel primo secolo d.C., era il cuore del divertimento e della spettacolarità romana." \
    "Qui si svolgevano combattimenti tra gladiatori, battaglie animali e perfino esecuzioni pubbliche! (...) " \
    "Ogni spettatore trovava la propria postazione, cullato dall'atmosfera di emozione che riempiva queste"\
    " mura. Ecco perché il Colosseo è ancora oggi un simbolo di potenza e grandezza romana!"
    
    motore.genera_audio(descrizione, "test_con_registro.wav")