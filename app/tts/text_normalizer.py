import re

class TextNormalizer:
    def __init__(self):
        # Uniamo più dizionari per ordine mentale
        self.replacements = {}
        
        # 1. TECNOLOGIA & INGLESE
        self.replacements.update({
            "xrtourguide": "ecs ar tur gaid",
            "futural": "fiu ciur al",
            "wi-fi": "uai fai",
            "ticket": "ticchet",
            "check-in": "cec in",
            "hall": "oll",
            "online": "on lain",
            "offline": "off lain",
            "touch": "tac",
            "location": "lochescion",
        })

        # 2. LATINO & MEDIEVALE (Architettura e Arte)
        self.replacements.update({
            # Edifici e Strutture
            "domus": "dòmus",           
            "insula": "ìnsula",
            "insulae": "ìnsule",        
            "castrum": "càstrum",
            "cardus": "càrdus",
            "decumanus": "decumànus",
            "forum": "fòrum",
            "basilica": "basìlica",     
            "atrium": "àtrium",
            "tablinum": "tablìnum",
            "triclinium": "triclìnium",
            "frigidarium": "frigidàrium",
            "calidarium": "calidàrium",
            "tepidarium": "tepidàrium",
            "vomitorium": "vomitòrium",
            "cavea": "càvea",
            
            # Arte e Iscrizioni
            "opus": "òpus",             
            "reticulatum": "reticulàtum",
            "incertum": "incèrtum",
            "fresco": "frèsco",
            "affresco": "affrèsco",
            "velarium": "velàrium",
            "lapidarium": "lapidàrium",
        })

        # 3. TERMINI ECCLESIASTICI / SACRI (Molto comuni nei musei)
        self.replacements.update({
            "sanctus": "sànctus",
            "pater": "pàter",
            "filius": "fìlius",
            "spiritus": "spìritus",
            "amen": "àmen",
            "gloria": "glòria",
            "magnificat": "magnìficat", 
            "requiem": "rècuiem",       
            "ecclesia": "ecclèsia",
            "cattedrale": "cattedràle",
            "duomo": "duòmo",
            "pieve": "piève",
            "presbiterio": "presbitèrio",
            "abside": "àbside",         
            "navata": "navàta",
            "transetto": "transètto",
            "cripta": "crìpta",
            "nartece": "nàrtece",
        })

       # 4. ESPRESSIONI STORICHE COMUNI
        self.replacements.update({
            "anno domini": "ànno dòmini",
            "ante christum": "ànte crìstum",
            "post christum": "pòst crìstum",
            "hic iacet": "hic iàcet",   
            "spqr": "esse pi qu erre",  
            "s.p.q.r.": "esse pi qu erre",
            "et": "et",                 
            "item": "ìtem",
            "ibidem": "ibìdem",
            "ex voto": "ecs vòto",
            
            # VARIANTI DATE (Con e senza punto finale)
            "d.c.": "dopo cristo",
            "d.c": "dopo cristo",    # Caso in cui manchi l'ultimo punto
            "a.c.": "avanti cristo",
            "a.c": "avanti cristo",
            "dc": "dopo cristo",     # Caso senza punti
            "ac": "avanti cristo"
        })

        #5. BRAND & PROGETTO
        self.replacements.update({
            "xrtourguide": "ekks ar tur gaid",
            "futural": "fiu ciur al",
            "xr": "ekks ar",
        })

    def _apply_replacements(self, text: str) -> str:
        for original, phonetic in self.replacements.items():
            pattern = r'(?i)'
            
            # 1. Se la chiave inizia con una lettera/numero, mettiamo il blocco all'inizio
            if original[0].isalnum():
                pattern += r'\b'
            
            pattern += re.escape(original)
        
            # Mettiamo il blocco alla fine (\b) SOLO se la chiave finisce con una lettera.
            # Se finisce con un punto (come "d.c."), NON lo mettiamo, così lo trova anche se c'è uno spazio dopo.
            if original[-1].isalnum():
                pattern += r'\b'
            
            text = re.sub(pattern, phonetic, text)
        return text
    
    def _fix_phonetic_glitches(self, text: str) -> str:
        """
        Invece di usare un dizionario, usiamo regole logiche per correggere
        intere categorie di suoni problematici per Piper.
        """
        
        # REGOLA: Gruppo "TR" Intervocalico
        # Cerca: una vocale + 'tr' + una vocale (es. piE-TRa, teA-TRo)
        # Sostituisce con: vocale + 't-tr' + vocale (Raddoppio tattico) o vocale + '-tr'
        
        # Spiegazione Regex:
        # (?i)         -> Ignora maiuscole/minuscole
        # ([a-zàèéìòù]) -> GRUPPO 1: Una lettera qualsiasi (o vocale accentata) prima
        # tr           -> Il suono problematico
        # ([a-zàèéìòù]) -> GRUPPO 2: Una lettera qualsiasi dopo
        
        # Strategia: Inseriamo un trattino per forzare la sillabazione "Pie-tra"
        # Nota: \1 richiama la lettera prima, \2 la lettera dopo.
        text = re.sub(r'(?i)([aeiouàèéìòù])tr([aeiouàèéìòù])', r'\1-tr\2', text)
        
        # Esempio risultato automatico:
        # "Pietra" -> "Pie-tra"
        # "Teatro" -> "Tea-tro"
        # "Vetro"  -> "Ve-tro"
        
        return text

    def clean_text(self, text: str) -> str:
        # 0. RIMOZIONE MARKDOWN E EMOJI
        # Rimuove asterischi, cancelletti, parentesi quadre (residui di prompt)
        text = re.sub(r'[\*\#\[\]\_\-]', '', text)
        
        # Rimuove qualsiasi carattere che NON sia:
        # - Lettere (a-z, A-Z, lettere accentate)
        # - Numeri
        # - Punteggiatura base (.,!?:;)
        # - Spazi
        # Questo elimina le Emoji.
        text = re.sub(r'[^\w\s\.,!\?;:àèéìòùÀÈÉÌÒÙ\'"\-]', '', text)

        # 1. Normalizzazione Dizionario
        text = self._apply_replacements(text)

        # NUOVO PASSAGGIO AUTOMATICO
        text = self._fix_phonetic_glitches(text)
        
        # 2. Pulizia Extra
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

if __name__ == "__main__":
    norm = TextNormalizer()
    test_phrases = [
        "Visitiamo la Domus del Chirurgo e il suo Atrium.",
        "Nell'Anno Domini 1200 fu costruita la Basilica.",
        "Il coro canta il Magnificat nell'abside.",
        "Iscrizione: Hic iacet un soldato del Castrum."
    ]
    
    print("--- TEST NORMALIZZAZIONE STORICA ---")
    for t in test_phrases:
        print(f"IN : {t}")
        print(f"OUT: {norm.clean_text(t)}\n")