import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np
import os
import tempfile
import requests
import openai
from PIL import Image
from modules.calculations import calculate_advanced_metrics
from modules.pdf_engine import BivaReportPDF
from modules.storage import get_patient_history, save_visit

# --- FUNZIONI GRAFICHE ---
def draw_body_map(pha_dx, pha_sx):
    fig, ax = plt.subplots(figsize=(4, 6))
    fig.patch.set_facecolor('white'); ax.set_facecolor('white')
    diff = 0
    if pha_dx > 0: diff = ((pha_dx - pha_sx) / pha_dx) * 100
    color_dx, color_sx = '#4ade80', '#4ade80'
    threshold = 3.0
    if diff > threshold: color_sx = '#ef4444' 
    elif diff < -threshold: color_dx = '#ef4444'

    ax.add_patch(patches.Circle((0.5, 0.9), 0.08, color='#ddd'))
    ax.add_patch(patches.Rectangle((0.5, 0.5), 0.15, 0.35, color=color_dx))
    ax.add_patch(patches.Rectangle((0.35, 0.5), 0.15, 0.35, color=color_sx))
    ax.add_patch(patches.Rectangle((0.68, 0.55), 0.08, 0.25, color=color_dx))
    ax.add_patch(patches.Rectangle((0.24, 0.55), 0.08, 0.25, color=color_sx))
    ax.add_patch(patches.Rectangle((0.52, 0.1), 0.11, 0.38, color=color_dx))
    ax.add_patch(patches.Rectangle((0.37, 0.1), 0.11, 0.38, color=color_sx))
    ax.text(0.2, 0.95, f"SX\n{pha_sx}°", color='black', fontsize=10, fontweight='bold', ha='center')
    ax.text(0.8, 0.95, f"DX\n{pha_dx}°", color='black', fontsize=10, fontweight='bold', ha='center')
    ax.set_title("ASIMMETRIA", fontsize=10, fontweight='bold', pad=10)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    return fig

# --- FUNZIONE DIAGNOSI ---
def run_clinical_diagnosis(data, name, subject_type, gender, age, weight, height, clinical_notes, data_sx=None):
    key = st.secrets.get("openai_key") or st.secrets.get("openai", {}).get("api_key")
    if not key: return "Errore API Key: Controlla i secrets."

    try:
        client = openai.Client(api_key=key)
        
        if data_sx:
            pha_dx = data['PhA']
            pha_sx = data_sx['PhA']
            diff_asym = abs(pha_dx - pha_sx)
            dati_strumentali_block = f"""
            - PhA LATO DESTRO: {pha_dx}°
            - PhA LATO SINISTRO: {pha_sx}°
            - ASIMMETRIA RILEVATA: {diff_asym:.2f}°
            - Rz DX: {data['Rz']} | Rz SX: {data_sx['Rz']}
            """
        else:
            dati_strumentali_block = f"""
            - PhA (Angolo di Fase): {data['PhA']}°
            - Rz: {data['Rz']} | Xc: {data['Xc']}
            """

        prompt = f"""
        Sei il Direttore Scientifico e Clinico di AREA199.
        Il tuo compito è analizzare i dati BIA (Bioimpedenziometria) e redigere un referto tecnico altamente specializzato.
        Il tuo tono è: Scientifico, Clinico, Oggettivo, Autoritario ("No Sugar-coating").

        DATI SOGGETTO:
        - Nome: {name}
        - Sesso: {gender}
        - Età: {age} anni
        - Sport/Attività: {subject_type}
        - Peso: {weight} kg | Altezza: {height} cm
        - Note Cliniche/Stato: {clinical_notes}

        DATI STRUMENTALI:
        {dati_strumentali_block}
        - BF%: {data['FM_perc']}% | FM: {data['FM_kg']} kg | FFM: {data['FFM_kg']} kg
        - TBW: {data['TBW_L']} L | ECW: {data['ECW_L']} L | ICW: {data['ICW_L']} L
        - BCM: {data['BCM_kg']} kg

        ISTRUZIONI DI ADATTAMENTO:
        1. SE ASIMMETRIA > 1.0°: Evidenzia il lato deficitario.
        2. SE ATLETA: Focus su Performance, Potenza, BCM.
        3. SE SEDENTARIO: Focus su Rischio metabolico, Infiammazione (ECW).
        4. SE CASI SPECIALI: Adatta in base alle note.

        --- INIZIO REFERTO ---
        1. QUADRO CLINICO E FUNZIONALE
        2. COMPOSIZIONE CORPOREA E TESSUTI
        3. STATO IDRATAZIONE E INFIAMMAZIONE
        4. STRATEGIA DI INTERVENTO
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1200
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Errore generazione: {str(e)}"

# --- FUNZIONE PRINCIPALE ---
def run_biva():
    st.markdown("""<style>
        .stMetric { background-color: #111; padding: 10px; border-left: 3px solid #E20613; }
        div[data-testid="stMetricValue"] { color: #E20613 !important; }
    </style>""", unsafe_allow_html=True)

    # --- IMMAGINI SENZA "assets/" ---
    if os.path.exists("logo_area199.png"): 
        st.sidebar.image("logo_area199.png", use_container_width=True)
    elif os.path.exists("logo_dark.jpg"):
        st.sidebar.image("logo_dark.jpg", use_container_width=True)
    
    st.sidebar.header("1. ANAGRAFICA")
    name = st.sidebar.text_input("Nome Cognome", "Mario Rossi")
    subject_type = st.sidebar.text_input("Attività / Sport", value="Sedentario")
    clinical_notes = st.sidebar.text_input("Note Cliniche", value="Nessuna")
    
    c1, c2 = st.sidebar.columns(2)
    gender = c1.selectbox("Sesso", ["M", "F"])
    age = c2.number_input("Età", 10, 99, 30)
    c3, c4 = st.sidebar.columns(2)
    h = c3.number_input("Altezza cm", 100.0, 230.0, 180.0)
    w = c4.number_input("Peso kg", 40.0, 150.0, 75.0)
    
    st.sidebar.markdown("---")
    st.sidebar.header("2. RILEVAZIONE")
    mode = st.sidebar.radio("Sensori", ["Standard (DX)", "Bilateral (DX+SX)"])
    
    c5, c6 = st.sidebar.columns(2)
    rz = c5.number_input("Rz DX", 0, 1000, 500)
    xc = c6.number_input("Xc DX", 0, 300, 50)
    
    rz_sx, xc_sx = 0.0, 0.0
    if mode == "Bilateral (DX+SX)":
        c7, c8 = st.sidebar.columns(2)
        rz_sx = c7.number_input("Rz SX", 0, 1000, 490)
        xc_sx = c8.number_input("Xc SX", 0, 300, 48)
        
    if st.sidebar.button("ELABORA REPORT"):
        st.session_state['analyzed'] = True
        st.session_state['data'] = calculate_advanced_metrics(rz, xc, h, w, age, gender)
        st.session_state['data_sx'] = calculate_advanced_metrics(rz_sx, xc_sx, h, w, age, gender) if mode == "Bilateral (DX+SX)" else None
        st.session_state['diagnosis'] = None

    if st.session_state.get('analyzed'):
        d = st.session_state['data']
        d_sx = st.session_state.get('data_sx')
        
        st.title(f"ANALISI: {name}")
        st.caption(f"Ref: Dott. Petruzzi | Profilo: {subject_type} | Note: {clinical_notes}")
        
        t1, t2, t3 = st.tabs(["DATI", "GRAFICI", "REFERTO"])
        
        with t1:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PhA", f"{d['PhA']}°")
            c2.metric("BF%", f"{d['FM_perc']}%") 
            c3.metric("SMM", f"{d['SMM_kg']} kg")
            c4.metric("TBW%", f"{d['TBW_perc']}%")
            
            st.dataframe(pd.DataFrame({
                "Parametro": ["FM (Grasso)", "FFM (Magro)", "BCM (Cellule)"],
                "Valore (kg)": [d['FM_kg'], d['FFM_kg'], d['BCM_kg']]
            }), hide_index=True)

        with t2:
            c_g1, c_g2 = st.columns(2)
            with c_g1:
                fig_biva, ax = plt.subplots(figsize=(4, 5))
                ax.scatter(d['Rz']/(h/100), d['Xc']/(h/100), c='red', s=100, label="DX")
                if d_sx: ax.scatter(d_sx['Rz']/(h/100), d_sx['Xc']/(h/100), c='cyan', s=80, label="SX")
                ax.invert_yaxis()
                ax.legend()
                st.pyplot(fig_biva)
            with c_g2:
                if mode == "Bilateral (DX+SX)" and d_sx:
                    fig_body = draw_body_map(d['PhA'], d_sx['PhA'])
                    st.pyplot(fig_body)

        with t3:
            if st.button("ELABORA REFERTO COMPLETO"):
                with st.spinner("Analisi..."):
                    res = run_clinical_diagnosis(d, name, subject_type, gender, age, w, h, clinical_notes, d_sx)
                    st.session_state['diagnosis'] = res
                    st.rerun()
            
            if st.session_state.get('diagnosis'):
                st.text_area("Testo", st.session_state['diagnosis'], height=600)

        st.markdown("---")
        c_s, c_p = st.columns(2)
        with c_s:
            if st.button("💾 ARCHIVIA"):
                try:
                    save_visit(name, w, rz, xc, d['PhA'], d['TBW_L'], d['FM_perc'], d['FFM_kg'])
                    st.success("Salvato")
                except: st.error("Errore DB")
        with c_p:
            if st.button("📄 CREA PDF"):
                biva_path = os.path.join(tempfile.gettempdir(), "biva.png")
                fig_biva.savefig(biva_path, dpi=150)
                
                body_path = None
                if mode == "Bilateral (DX+SX)" and d_sx and 'fig_body' in locals():
                    body_path = os.path.join(tempfile.gettempdir(), "body.png")
                    fig_body.savefig(body_path, dpi=150)
                
                pdf = BivaReportPDF(name)
                pdf_data = d.copy()
                pdf_data['Report_Text'] = st.session_state.get('diagnosis', "")
                pdf.generate_body(pdf_data, graph1_path=biva_path, body_map_path=body_path)
                
                st.download_button("SCARICA PDF", bytes(pdf.output(dest='S')), f"Referto_{name}.pdf", "application/pdf")
