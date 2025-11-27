from fastapi import FastAPI, HTTPException
from contextlib import asynccontextmanager
import os
import hashlib
import uvicorn

# Schemas aggiornati
from app.schemas import (
    TitleRequest, TitleResponse, 
    DescriptionRequest, DescriptionResponse,
    AudioGenerationRequest, AudioGenerationResponse
)

# Services
from app.llm.services.optimize_title import generate_optimized_title
from app.llm.services.optimize_description import generate_optimized_description
from app.tts.coqui_engine import XttsEngine 
from app.storage import check_file_exists, get_file_url, upload_file

# --- VARIABILI GLOBALI ---
tts_engine = None

# --- LIFESPAN ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    global tts_engine
    print("Avvio Backend...")

    # Carichiamo XTTS solo se abbiamo intenzione di servire audio
    tts_engine = XttsEngine() 
    print("XTTS Ready.")
    
    yield
    print("Shutdown.")

app = FastAPI(title="XRTourGuide API", lifespan=lifespan)

# --- ENDPOINTS ---

@app.get("/")
def root():
    """Verifica se il server è vivo"""
    return {
        "status": "online", 
        "service": "XRTourGuide TTS", 
    }

@app.post("/generate-audio", response_model=AudioGenerationResponse)
async def generate_audio_ondemand(request: AudioGenerationRequest):
    """
    Chiamato dall'App del turista quando serve l'audio.
    Input: Una frase di testo.
    Output: URL MP3 (Generato al volo o recuperato da Cache MinIO).
    """
    global tts_engine
    
    if tts_engine is None:
        raise HTTPException(status_code=503, detail="Servizio TTS non attivo")

    # 1. Calcolo Hash (Impronta digitale della frase)
    text_hash = hashlib.md5(request.text.encode('utf-8')).hexdigest()
    
    # 2. Definizione Percorso MinIO (es:a1b2c3d4.mp3)

    object_name = f"{text_hash}.mp3"
    
    # 3. STRATEGIA CACHE: Controllo se esiste già
    if check_file_exists(object_name):
        print(f"CACHE HIT: {object_name}")
        return AudioGenerationResponse(
            audio_url=get_file_url(object_name),
            cached=True
        )
    
    # 4. GENERAZIONE (Se non esiste)
    print(f"NEW TTS: Generazione per '{request.text:20}'...")
    
    local_temp = f"temp_{text_hash}.mp3"
    
    # XTTS Engine (Genera WAV -> Converte MP3)
    success = tts_engine.generate_audio(request.text, local_temp)
    
    if not success or not os.path.exists(local_temp):
        raise HTTPException(status_code=500, detail="Fallimento generazione audio")
    
    # Upload su MinIO
    upload_file(local_temp, object_name)
    
    # Pulizia locale
    os.remove(local_temp)
    
    # Ritorna URL
    return AudioGenerationResponse(
        audio_url=get_file_url(object_name),
        cached=False
    )


@app.post("/optimize/title", response_model=TitleResponse)
async def optimize_title_endpoint(request: TitleRequest):
    """
        Riceve un titolo scritto dall'autore del tour e ne restituisce 3 varianti ottimizzate secondo i patter scelti
    """

    if not request.original_title:
        raise HTTPException(status_code=400, detail="Il titolo non può essere vuoto")
        
    # Chiamata al servizio LLM
    result = generate_optimized_title(request.original_title)
    
    return result

@app.post("/optimize/description", response_model=DescriptionResponse)
async def optimize_description_endpoint(request: DescriptionRequest):
    """
    Riceve una descrizione grezza e restituisce:
    1. Testo bello per la UI.
    2. Chunk audio pronti per XTTS.
    """
    if not request.original_text:
        raise HTTPException(status_code=400, detail="Il testo non può essere vuoto")
    
    # Chiamata al servizio
    result = generate_optimized_description(request.original_text)
    
    return result

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)