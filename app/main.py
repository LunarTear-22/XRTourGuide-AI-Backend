from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import hashlib
from pathlib import Path
from app.tts.piper_engine import PiperEngine

# 1. Configurazione Iniziale
app = FastAPI(
    title="XRTourGuide AI API",
    description="Backend TTS per il progetto XRTourGuide",
    version="1.1.0"
)

# --- CONFIGURAZIONE CACHE ---
TEMP_AUDIO_DIR = "generated_audio"
MAX_CACHE_FILES = 50  # Numero massimo di file mp3 da mantenere. Modifica a piacere!
FILES_TO_DELETE= 10

if not os.path.exists(TEMP_AUDIO_DIR):
    os.makedirs(TEMP_AUDIO_DIR)

# 2. Inizializzazione Motore TTS
try:
    tts_engine = PiperEngine()
    print("Motore TTS caricato correttamente nel backend.")
except Exception as e:
    print(f"ERRORE CRITICO ALL'AVVIO: {e}")
    tts_engine = None

# 3. Modello Dati
class TourRequest(BaseModel):
    text: str
    language: str = "it"

# --- FUNZIONE DI PULIZIA (LRU) ---
def pulisci_cache_se_piena():
    """
    Controlla se abbiamo troppi file. Se sì, cancella i più vecchi (quelli non usati da tempo).
    """
    try:
        # Lista di tutti gli mp3 con percorso completo
        files = [os.path.join(TEMP_AUDIO_DIR, f) for f in os.listdir(TEMP_AUDIO_DIR) if f.endswith('.mp3')]
        
        num_files=len(files)

        # Se siamo sotto il limite, tutto ok
        if len(files) < MAX_CACHE_FILES:
            return

        # Ordina i file in base all'ultima modifica (dal più vecchio al più nuovo)
        files.sort(key=os.path.getmtime)

        # 3. Calcola quanti file audio cancellare
        da_cancellare = min(FILES_TO_DELETE, num_files)

        count_rimossi = 0
        for i in range(da_cancellare):
            file_vecchio = files[i]
            try:
                os.remove(file_vecchio)
                count_rimossi += 1
            except OSError as e:
                print(f"Impossibile cancellare {file_vecchio}: {e}")
        
        print(f"Pulizia completata: rimossi {count_rimossi} file vecchi. Spazio liberato.")
            
    except Exception as e:
        print(f"Errore critico durante pulizia cache: {e}")

# --- ENDPOINTS ---

@app.get("/")
def root():
    """Verifica se il server è vivo"""
    return {
        "status": "online", 
        "service": "XRTourGuide TTS", 
        "cache_limit": MAX_CACHE_FILES
    }

@app.post("/api/generate-audio")
async def generate_audio(request: TourRequest):
    """
    Riceve un testo JSON -> Restituisce il file audio .mp3 (usando la cache se possibile)
    """
    if tts_engine is None:
        raise HTTPException(status_code=500, detail="Motore TTS non inizializzato")

    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Il testo non può essere vuoto")

    try:
        # 1. CALCOLO HASH (Impronta digitale del testo)
        hash_object = hashlib.md5(request.text.encode())
        filename = f"{hash_object.hexdigest()}.mp3"
        file_path = os.path.join(TEMP_AUDIO_DIR, filename)

        # 2. CONTROLLO CACHE (Hit)
        if os.path.exists(file_path):
            print(f"CACHE HIT: Audio già pronto per '{filename}'")
            
            # TRUCCO LRU: "Tocchiamo" il file per aggiornare la data di modifica.
            # Così il sistema sa che è stato usato di recente e non lo cancellerà subito.
            Path(file_path).touch()
            
            return FileResponse(file_path, media_type="audio/mpeg", filename="tour_guide.mp3")

        # 3. CACHE MISS -> Generazione Nuova
        print(f"NUOVA GENERAZIONE: Creazione audio per '{filename}'")
        
        # Facciamo spazio se serve
        pulisci_cache_se_piena()

        # Chiamiamo Piper (che farà anche la conversione MP3)
        successo = tts_engine.genera_audio(request.text, file_path)

        if not successo:
            raise HTTPException(status_code=500, detail="Errore interno generazione audio")

        return FileResponse(
            file_path, 
            media_type="audio/mpeg", 
            filename="tour_guide.mp3"
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore Server: {str(e)}")