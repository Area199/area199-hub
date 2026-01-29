import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import datetime

def get_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def clean_float(value):
    """Pulisce i numeri da virgole e simboli"""
    if value is None or str(value).strip() == "": return 0.0
    # Sostituisce la virgola con il punto
    s_val = str(value).replace(',', '.').replace('%', '').strip()
    try:
        return float(s_val)
    except:
        return 0.0

def get_patient_history(patient_name):
    """Recupera lo storico da AREA199_DB"""
    try:
        client = get_client()
        # PUNTA DRITTO AL FILE CORRETTO
        sh = client.open("AREA199_DB")
        worksheet = sh.worksheet("BIVA_LOGS")
        
        # Legge tutto come testo per evitare errori di formato
        data = worksheet.get_all_values()
        
        if not data or len(data) < 2: return pd.DataFrame()
            
        # Intestazioni (Riga 1)
        headers = [str(h).strip().lower() for h in data[0]] 
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # Cerca la colonna Paziente/Nome
        col_name = None
        for c in df.columns:
            if "paziente" in c or "nome" in c or "soggetto" in c:
                col_name = c
                break
        
        if not col_name: return pd.DataFrame()

        # Filtra per nome
        target_name = patient_name.strip().lower()
        df_filtered = df[df[col_name].astype(str).str.strip().str.lower() == target_name].copy()
        
        if df_filtered.empty: return pd.DataFrame()

        # Mappa le colonne standard
        map_cols = {
            'PhA': ['pha', 'phase', 'angolo'],
            'FM%': ['fm%', 'bf%', 'massa grassa %', 'fat%'],
            'TBW': ['tbw', 'acqua', 'water'],
            'Peso': ['peso', 'weight', 'kg'],
            'Data': ['data', 'date']
        }
        
        final_df = df_filtered.copy()
        for std_key, possible_names in map_cols.items():
            for col in final_df.columns:
                if col in possible_names:
                    final_df.rename(columns={col: std_key}, inplace=True)
                    if std_key != 'Data':
                        # Applica la pulizia virgola -> punto
                        final_df[std_key] = final_df[std_key].apply(clean_float)
                    break
        
        return final_df

    except Exception as e:
        # st.error(f"Errore DB: {e}")
        return pd.DataFrame()

def save_visit(name, weight, rz, xc, pha, tbw, fm_perc, ffm_kg):
    try:
        client = get_client()
        sh = client.open("AREA199_DB") # NOME CORRETTO
        worksheet = sh.worksheet("BIVA_LOGS")
        
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Salviamo convertendo i punti in virgole per Excel italiano, o viceversa.
        # Qui salvo come stringhe per sicurezza massima.
        row = [
            date_str, 
            name, 
            str(weight).replace('.', ','), 
            str(int(rz)), 
            str(int(xc)), 
            str(pha).replace('.', ','), 
            str(tbw).replace('.', ','), 
            str(fm_perc).replace('.', ','), 
            str(ffm_kg).replace('.', ',')
        ]
        
        worksheet.append_row(row)
        return True
    except Exception as e:
        st.error(f"Errore salvataggio: {e}")
        return False
