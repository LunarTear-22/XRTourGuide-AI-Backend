from pydantic import BaseModel
from typing import List

    #--- TITOLI ---

class TitleRequest(BaseModel):
    original_title: str
    
class TitleResponse(BaseModel):
    original: str
    options: List[str] # Restituiremo 3 varianti
    best_option: str


    # --- DESCRIZIONI ---

class DescriptionRequest(BaseModel):
    original_text: str     
    target_lang: str = "it" # Per ora default italiano

class DescriptionResponse(BaseModel):
    full_text_optimized: str  # Testo intero da mostrare a schermo (UI)
    tts_chunks: List[str]     # Lista di frasi <180char per il motore audio