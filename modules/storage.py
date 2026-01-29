import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import streamlit as st
import datetime
import re

def get_client():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
    return gspread.authorize(creds)

def clean_float(value):
    """Pulisce i numeri da virgole e %"""
    if value is None: return 0.0
    s_val = str(value).replace(',', '.')
    # Toglie tutto quello che non è numero o punto (es. "18.5%" -> "18.5")
    s_val = re.sub(r'[^\d\.-]', '', s_val)
    try:
        return float(s_val)
    except:
        return 0.0

def get_patient_history(patient_name):
    """Recupera lo storico mappando ESATTAMENTE le tue colonne"""
    try:
        client = get_client()
        sh = client.open("AREA199_DB")
        worksheet = sh.worksheet("BIVA_LOGS")
        
        data = worksheet.get_all_values()
        if not data or len(data) < 2: return pd.DataFrame()
            
        # Intestazioni originali (senza toccarle troppo, solo strip)
        headers = [str(h).strip() for h in data[0]] 
        rows = data[1:]
        df = pd.DataFrame(rows, columns=headers)
        
        # Cerca la colonna Paziente (flessibile sul nome colonna paziente)
        col_name = None
        for c in df.columns:
            if c.lower() in ["paziente", "nome", "soggetto", "name"]:
                col_name = c
                break
        if not col_name: return pd.DataFrame()

        # Filtra per nome paziente
        target_name = patient_name.strip().lower()
        df_filtered = df[df[col_name].astype(str).str.strip().str.lower() == target_name].copy()
        
        if df_filtered.empty: return pd.DataFrame()

        # --- MAPPA ESATTA: TUE COLONNE -> CHIAVI SISTEMA ---
        # Sinistra: Chiave che usa il PDF / Destra: Nome esatto nel tuo Excel/Drive
        exact_map = {
            'Data':    'Data',
            'Weight':  'Peso',
            'Rz':      'Rz',
            'Xc':      'Xc',
            'PhA':     'PhA',
            'TBW_L':   'TBW',
            'FM_perc': 'FM%',
            'FFM_kg':  'FFM',
            'BCM_kg':  'BCM' # Se presente
        }
        
        final_df = pd.DataFrame()
        
        # Costruisce il dataframe finale traducendo le colonne
        for pdf_key, sheet_col in exact_map.items():
            # Cerca la colonna nel foglio (case insensitive per sicurezza)
            found_col = None
            for c in df_filtered.columns:
                if c.lower() == sheet_col.lower():
                    found_col = c
                    break
            
            if found_col:
                if pdf_key == 'Data':
                    final_df[pdf_key] = df_filtered[found_col]
                else:
                    final_df[pdf_key] = df_filtered[found_col].apply(clean_float)
            else:
                # Se manca la colonna, metti 0.0
                if pdf_key != 'Data':
                    final_df[pdf_key] = 0.0
        
        # Aggiungiamo anche la chiave 'Date' (inglese) per compatibilità
        if 'Data' in final_df.columns:
            final_df['Date'] = final_df['Data']

        return final_df

    except Exception as e:
        return pd.DataFrame()

def save_visit(name, weight, rz, xc, pha, tbw, fm_perc, ffm_kg):
    try:
        client = get_client()
        sh = client.open("AREA199_DB")
        worksheet = sh.worksheet("BIVA_LOGS")
        
        date_str = datetime.datetime.now().strftime("%d/%m/%Y")
        
        # Ordine ESATTO delle colonne che mi hai dato:
        # Data, Paziente, Peso, Rz, Xc, PhA, TBW, FM%, FFM
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
