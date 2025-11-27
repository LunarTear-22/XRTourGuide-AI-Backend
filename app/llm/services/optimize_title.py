import ollama
import json
from app.schemas import TitleResponse

MODEL_NAME = "qwen2.5:7b"

def generate_optimized_title(original_title: str) -> TitleResponse:
    
    # --- 1. PATTERN: PERSONA ---
    persona = (
        "Sei uno storico dell'arte specializzato in turismo ed in storytelling. "
        "Il tuo stile è conciso, evocativo e moderno. "
        "Sai trasformare termini noiosi in interessanti ed accattivanti."
    )

    # --- 2. PATTERN: AUDIENCE  ---
    audience = (
        "Il tuo pubblico sono turisti curiosi che usano lo smartphone per visualizzare i contenuti in AR. "
        "I titoli devono catturarli in meno di 1 secondo. "
        "Evita linguaggio troppo accademico o troppo formale."
    )

    # --- 3. PATTERN: CONTEXT MANAGER  ---
    context = (
        f"Il titolo attuale '{original_title}' è troppo generico o poco attraente. "
        "Obiettivo: Generare varianti che spingano l'utente a cliccare per saperne di più."
    )

    # --- 4. PATTERN: TEMPLATE (Format)  ---
    template = """
    FORMATO OUTPUT RICHIESTO (JSON PURO):
    Devi restituire SOLO un oggetto JSON con questa struttura esatta, senza altro testo prima o dopo:
    {
        "options": [
            "Titolo Corto & Punchy (Max 25 car)",
            "Titolo Evocativo/Misterioso",
            "Titolo Domanda/Ingaggio"
        ],
        "best_option": "La migliore delle tre"
    }
    """

    # --- ASSEMBLAGGIO DEL PROMPT ---
    full_prompt = f"""
    {persona}
    {audience}
    {context}
    
    TASK: Riscrivi il titolo '{original_title}'.
    
    {template}
    """

    print(f" Chiamata a {MODEL_NAME} per ottimizzazione titoli...")

    # Chiamata a Ollama
    response = ollama.chat(model=MODEL_NAME, messages=[
        {'role': 'user', 'content': full_prompt},
    ])

    raw_content = response['message']['content']
    
    # Parsing del JSON (Pulizia nel caso di refusi)
    try:
        # pulizia ```json ... ```,
        clean_json = raw_content.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        return TitleResponse(
            original=original_title,
            options=data["options"],
            best_option=data["best_option"]
        )
    except Exception as e:
        print(f" Errore parsing JSON: {e}")
        # Fallback in caso di errore
        return TitleResponse(
            original=original_title,
            options=[original_title], 
            best_option=original_title
        )