import subprocess
import os

#Da prevedere un dizionario per normalizzare la pronuncia di alcune parole inglesi

def genera_audio_piper(testo, output_filename):
    model_path = "it_IT-paola-medium.onnx"
    
    if not os.path.exists(model_path):
        print(f"ERRORE: Manca il file {model_path}")
        return False

    print(f"Generazione audio per: '{testo[:30]}...'")

    # 2. Comando da eseguire
    comando = [
        "python", "-m", "piper",
        "--model", model_path,
        "--output_file", output_filename,     
    ]

    # --- FIX CODIFICA WINDOWS ---
    # forza Python a usare UTF-8, garantisce la lettura corretta delle vocali accentate
    my_env = os.environ.copy()
    my_env["PYTHONUTF8"] = "1"
    my_env["PYTHONIOENCODING"] = "utf-8"

    try:
        processo = subprocess.Popen(
            comando, 
            stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            env=my_env
        )
        
        # Inviamo il testo
        stdout, stderr = processo.communicate(input=testo.encode('utf-8'))

        # 4. Controllo Errori
        if processo.returncode != 0:
            print("Errore durante la generazione:")
            print(stderr.decode('utf-8'))
            return False
            
        # 5. Controllo se il file esiste ed è > 0 bytes
        if os.path.exists(output_filename) and os.path.getsize(output_filename) > 1000:
            print(f"Audio generato con successo: {output_filename}")
            print(f"Dimensione: {os.path.getsize(output_filename)} bytes")
            return True
        else:
            print("Il file è stato creato ma sembra vuoto.")
            return False

    except FileNotFoundError:
        print("Errore: Non trovo 'python'. Sei sicuro di essere nell'ambiente virtuale giusto?")
        return False

# --- TEST ---
if __name__ == "__main__":
    # Testo del tour
    testo_tour = "Benvenuti nella maestosa Cappella Sistina! Questo è il vero cuore pulsante dei Musei Vaticani. " \
    "Vi invito ora ad alzare lo sguardo verso la volta. Quello che vedete sopra di voi non è solo " \
    "un affresco, ma il capolavoro assoluto di Michelangelo Buonarroti."
    
    # Nome file uscita
    file_audio = "audio_backend_paola.wav"
    
    # Eseguiamo
    genera_audio_piper(testo_tour, file_audio)

