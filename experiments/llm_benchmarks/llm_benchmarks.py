import requests
import time
import json
import csv
import re
import statistics

# --- CONFIGURAZIONE MODELLI ---
MODELS = [
    "qwen2.5:7b",     
    "llama3.1:8b",    
    "mistral-nemo", #(ELIMINATO TROPPO LENTO)  
    "phi3.5"         
]

OUTPUT_FILE = "benchmark_advanced_results.csv"

# --- PROMPT  ---
SYSTEM_PROMPT = """
### PATTERN: PERSONA
Agisci come un esperto di storia dell'arte empatico e carismatico.
Il tuo compito è revisionare ed espandere la descrizione fornita dall'utente.
Non sei un'enciclopedia, sei un narratore che accompagna il visitatore.

### PATTERN: AUDIENCE
Il tuo pubblico è composto da turisti generici, famiglie e curiosi. 
Evita il gergo accademico complesso. Usa un linguaggio caldo e accessibile.

### PATTERN: CONTEXT MANAGER
Rimani strettamente focalizzato sul monumento descritto in input.
**Mantieni le informazioni fattuali corrette fornite in input, ma rendile più avvincenti.**

### PATTERN: TEMPLATE & OUTPUT AUTOMATION
Devi rispondere ESCLUSIVAMENTE con un oggetto JSON valido. 
Non aggiungere saluti, premesse o testo fuori dal JSON.
Struttura richiesta:
{
  "titolo": "Un titolo accattivante basato sul testo (max 60 caratteri)",
  "descrizione_audio": "Il testo narrativo revisionato...",
  "fact_check": ["Lista array di date, nomi o fatti citati per verifica"]
}

### LUNGHEZZA OUTPUT
L'obiettivo è una durata di circa 1 minuto di parlato (tra le 130 e le 160 parole).
Se l'input è troppo breve, espandilo con dettagli sensoriali o storici pertinenti.
Se l'input è troppo lungo, sintetizzalo mantenendo i punti chiave.

### PUNCTUATION ENGINEERING (Regia Audio per TTS)
Scrivi il campo 'descrizione_audio' ottimizzato ESPLICITAMENTE per la lettura vocale:
1. Usa frequentemente i tre puntini (...) per indicare pause di respiro e suspense.
2. Usa punti esclamativi (!) per enfatizzare le emozioni.
3. Spezza le frasi lunghe in frasi brevi.
4. NON usare mai elenchi puntati, parentesi o numeri (es. "1200" -> "milleduecento").
"""

USER_INPUT = "Il Colosseo è un anfiteatro romano del primo secolo. Era usato per i giochi."

def extract_json_segment(text):
    """
    Cerca di estrarre il blocco JSON anche se il modello scrive altro testo attorno.
    Usa Regex per trovare la prima { e l'ultima }.
    """
    try:
        # Rimuove blocchi markdown tipo ```json ... ```
        text = re.sub(r"```json|```", "", text).strip()
        
        # Cerca il contenuto tra la prima graffa aperta e l'ultima chiusa
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            return match.group(1)
        return text # Se non trova nulla, ridà il testo grezzo sperando vada bene
    except:
        return text



def analyze_adherence(response_text):
    """
    Valutazione Avanzata v2.0
    Analizza: JSON, Ritmo, Emotività, Lunghezza Frasi, Divieti.
    """
    score = 0
    errors = []
    json_data = None

    # --- 1. JSON INFRASTRUCTURE (40 Punti) ---
    # Senza questo, il resto non conta.
    try:
        clean_text = re.sub(r"```json|```", "", response_text).strip()
        # Tenta di estrarre il JSON se c'è testo sporco attorno
        match = re.search(r'(\{.*\})', clean_text, re.DOTALL)
        if match:
            clean_text = match.group(1)
        
        json_data = json.loads(clean_text)
        score += 25 # JSON Valido
    except json.JSONDecodeError:
        return 0, "CRITICAL: No JSON"

    required_keys = ["titolo", "descrizione_audio", "fact_check"]
    if all(key in json_data for key in required_keys):
        score += 15 # Chiavi corrette
    else:
        missing = [k for k in required_keys if k not in json_data]
        errors.append(f"MISSING_KEYS({missing})")

    # Estraiamo la descrizione per l'analisi linguistica
    desc = json_data.get("descrizione_audio", "")
    word_count = len(desc.split())
    
    # Se la descrizione è vuota, inutile continuare
    if word_count == 0:
        return score, "EMPTY_DESC"

    # --- 2. PAUSE & RITMO (20 Punti) ---
    # Vogliamo almeno 1 "..." ogni 40 parole circa, o un minimo assoluto di 3
    dots_count = desc.count("...")
    if dots_count >= 3:
        score += 20
    elif dots_count >= 1:
        score += 10
        errors.append("LOW_PAUSES")
    else:
        errors.append("NO_PAUSES")

    # --- 3. EMOTIVITÀ (10 Punti) ---
    # Piper è piatto se non usi punti esclamativi.
    exclam_count = desc.count("!")
    if exclam_count >= 2:
        score += 10
    elif exclam_count == 1:
        score += 5
    else:
        errors.append("FLAT_TONE (No '!')")

    # --- 4. RESPIRABILITÀ / FRASI CORTE (15 Punti) ---
    # Spezziamo il testo in frasi (usando . ! ? come delimitatori)
    sentences = re.split(r'[.!?]+', desc)
    # Filtriamo frasi vuote
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if sentences:
        avg_len = statistics.mean([len(s.split()) for s in sentences])
        
        if avg_len <= 20:       # Ottimo: frasi brevi
            score += 15
        elif avg_len <= 30:     # Accettabile
            score += 10
        else:                   # Pessimo: frasi infinite (>30 parole)
            score += 0
            errors.append(f"LONG_SENTENCES (Avg {avg_len:.1f} words)")
    else:
        errors.append("NO_SENTENCES")

    # --- 5. TARGET LUNGHEZZA (15 Punti) ---
    # Target: 130-180 parole. Accettabile: 100-220.
    if 120 <= word_count <= 180:
        score += 15
    elif 100 <= word_count <= 220:
        score += 10
    elif word_count < 100:
        score += 5
        errors.append("TOO_SHORT")
    else:
        score += 5
        errors.append("TOO_LONG")

    # --- 6. PENALITÀ (Sottrazione Punti) ---
    # Controllo elenchi puntati (vietatissimi per TTS narrativo)
    if re.search(r'^[\s]*[\*\-]\s', desc, re.MULTILINE):
        score -= 20
        errors.append("BULLET_POINTS_DETECTED")

    # Cap (Il voto non può superare 100 o andare sotto 0)
    score = max(0, min(100, score))

    return score, ", ".join(errors) if errors else "PERFECT"

def run_benchmark():
    print(f"Avvio Benchmark v3.0 su {len(MODELS)} modelli...")
    print(f"Test Pattern: Persona, Audience, Context, Template, FactCheck.\n")

    with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow([
            "Modello", 
            "Score (0-100)", 
            "Note Errori",
            "Velocità (Tok/s)", 
            "Tempo Totale (s)",
            "Output Preview"
        ])

        for model in MODELS:
            print(f"--- Testing: {model} ---")
            
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": USER_INPUT}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.3, # Basso per favorire il JSON
                    "num_ctx": 4096     # Contesto sufficiente
                }
            }

            try:
                start = time.time()
                response = requests.post("http://localhost:11434/api/chat", json=payload)
                
                # Gestione Errori HTTP
                if response.status_code != 200:
                    print(f"   Errore API: {response.status_code} - {response.text}")
                    writer.writerow([model, 0, f"API ERROR {response.status_code}", 0, 0, ""])
                    continue

                res_json = response.json()

                # Gestione Errori Ollama
                if "error" in res_json:
                    print(f"   Errore Ollama: {res_json['error']}")
                    writer.writerow([model, 0, f"OLLAMA ERROR: {res_json['error']}", 0, 0, ""])
                    continue

                # Estrazione Dati
                if "message" in res_json:
                    content = res_json["message"]["content"]
                    eval_dur = res_json.get("eval_duration", 1) / 1e9
                    eval_count = res_json.get("eval_count", 1)
                    tps = eval_count / eval_dur if eval_dur > 0 else 0
                    total_time = res_json.get("total_duration", 0) / 1e9

                    # Analisi Qualità
                    quality_score, error_report = analyze_adherence(content)

                    print(f"    Score: {quality_score}/100")
                    print(f"    Speed: {tps:.2f} t/s")
                    if quality_score < 100:
                        print(f"    Issues: {error_report}")

                    writer.writerow([
                        model,
                        quality_score,
                        error_report,
                        f"{tps:.2f}",
                        f"{total_time:.2f}",
                        content
                    ])
                else:
                    print("    Risposta malformata (niente message)")

            except Exception as e:
                print(f"    Errore critico Python: {e}")
                writer.writerow([model, 0, f"PYTHON CRASH: {str(e)}", 0, 0, ""])

    print(f"\n Benchmark completato. Risultati in: {OUTPUT_FILE}")

if __name__ == "__main__":
    # Check rapido se Ollama è vivo
    url_check = "http://127.0.0.1:11434" 
    try:
        print(f"Cerco Ollama su {url_check}...")
        requests.get(url_check)
        print(" Ollama trovato! Avvio benchmark...")
        run_benchmark()
    except Exception as e: 
        print(f"\n ERRORE DI CONNESSIONE: Python non riesce a contattare Ollama.")
        print(f"Dettaglio tecnico: {e}")
        print("\nSOLUZIONE:")
        print("1. Apri una NUOVA finestra di PowerShell.")
        print("2. Scrivi 'ollama serve' e premi Invio.")
        print("3. Lascia quella finestra APERTA e riprova qui.")