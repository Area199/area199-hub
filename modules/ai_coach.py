import streamlit as st
from openai import OpenAI
import os

def generate_ai_report(data_dict, patient_name):
    """
    Versione 'UNIVERSALE' che legge la chiave 'openai_key' definita dall'utente.
    """
    
    # --- 1. CACCIA ALLA CHIAVE (DEBUGGING) ---
    api_key = None
    
    # CASO TUA APP: Cerchiamo esattamente 'openai_key' come hai scritto tu
    if "openai_key" in st.secrets:
        api_key = st.secrets["openai_key"]
        
    # Caso Standard Streamlit (per sicurezza)
    elif "openai" in st.secrets and "api_key" in st.secrets["openai"]:
        api_key = st.secrets["openai"]["api_key"]
        
    # Caso Variabile d'ambiente
    elif "OPENAI_API_KEY" in os.environ:
        api_key = os.environ["OPENAI_API_KEY"]

    # SE ANCORA NON LA TROVA:
    if not api_key:
        return "⚠️ ERRORE: Non trovo la chiave 'openai_key' nei Secrets. Controlla di averla incollata senza errori."

    # --- 2. CONNESSIONE AI ---
    try:
        # Inizializza il client con la chiave trovata
        client = OpenAI(api_key=api_key)
        
        # Preparazione dati sicura (tutto stringa per evitare crash)
        pha = str(data_dict.get('PhA', 'N/D'))
        tbw = str(data_dict.get('TBW_perc', 'N/D'))
        fm = str(data_dict.get('FM_perc', 'N/D'))
        ffm = str(data_dict.get('FFM_kg', 'N/D'))

        # Prompt per l'AI
        prompt = f"""
        Sei il Performance Specialist di AREA199.
        Analizza i dati BIA di {patient_name}:
        - Angolo di Fase: {pha}°
        - Idratazione: {tbw}%
        - Massa Grassa: {fm}%
        - Massa Magra: {ffm} kg
        
        Scrivi un report tecnico e motivante in 3 punti elenco.
        Focus su performance e salute cellulare.
        """

        # Chiamata API (Uso gpt-4o-mini o gpt-3.5-turbo che sono rapidi)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", 
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=300
        )
        
        return response.choices[0].message.content

    except Exception as e:
        # Questo comando evita lo schermo nero e ti stampa l'errore rosso
        return f"❌ ERRORE DI CONNESSIONE OPENAI: {str(e)}"
