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

# --- FUNZIONI GRAFICHE (Fuori dalla funzione principale per pulizia) ---
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

# --- FUNZIONE DIAGNOSI (Con il tuo Prompt Originale) ---
def run_clinical_diagnosis(data, name, subject_type, gender, age, weight, height, clinical_notes, data_sx=None):
    # Recupero chiave sicuro per il modulo
    key = st.secrets.get("openai_key") or st.secrets.get("openai", {}).get("api_key")
    if not key: return "Errore API Key: Controlla i secrets."

    try:
        client = openai.Client(api_key=key)
        
        # 1. GESTIONE BILATERALE DINAMICA
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

        # 2. PROMPT CLINICO ORIGINALE
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

        ISTRUZIONI DI ADATTAMENTO (IL TUO CERVELLO):
        Prima di scrivere, analizza il profilo del soggetto e ADATTA la tua analisi secondo queste regole:

        1. SE C'È ASIMMETRIA EVIDENTE (> 1.0° di differenza tra DX e SX):
           - NON basare l'analisi solo sul valore più alto (sano).
           - EVIDENZIA il lato sofferente (quello con PhA più basso).
           - Scrivi chiaramente: "Rilevata forte asimmetria funzionale. Il lato [Destro/Sinistro] presenta deficit cellulare (PhA basso) rispetto al lato sano".
           - Collega questo dato all'infortunio se presente nelle Note.

        2. SE ATLETA (Agonista/Amatore):
           - Focus: Performance, Potenza, Recupero, Carico di Glicogeno.
           - Obiettivo: Massimizzare BCM e PhA.
           - Linguaggio: "Ottimizzazione", "Riatletizzazione", "Potenziale".

        3. SE SEDENTARIO / SOVRAPPESO:
           - Focus: Rischio metabolico, Infiammazione silente (ECW alta), Sarcopenia.
           - Obiettivo: Riduzione FM, Attivazione metabolica.
           - Linguaggio: Medico-preventivo, Urgenza di intervento.

        4. SE CASI SPECIALI (Gravidanza / Patologia / Protesi / Infortunio):
           - Infortunio: Focus su infiammazione locale (ECW) e perdita di tono (PhA basso sul lato leso).
           - Gravidanza: Focus assoluto su TBW e ECW. Ignora BF%.

        --- INIZIO REFERTO (Scrivi direttamente il testo strutturato) ---

        1. QUADRO CLINICO E FUNZIONALE
        [Analizza lo stato generale incrociando i dati. Se c'è asimmetria, inizia SUBITO parlando di quella. Definisci se il soggetto è "In salute", "Infiammato" o "Infortunato". NON USARE MAI IL NOME DEL PAZIENTE.]

        2. COMPOSIZIONE CORPOREA E TESSUTI
        [Analizza BF% e BCM. C'è troppa massa grassa o troppo poco muscolo?]

        3. STATO IDRATAZIONE E INFIAMMAZIONE
        [Analizza ECW vs ICW. ECW Alta = Infiammazione/Stress.]

        4. STRATEGIA DI INTERVENTO (Action Plan)
        [Dai 3 direttive pratiche. Se c'è asimmetria, includi "Protocollo di recupero per l'arto deficitario".]
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

# --- FUNZIONE PRINCIPALE (Il "Contenitore" per il Hub) ---
def run_biva():
    # Stili CSS locali
    st.markdown("""<style>
        .stMetric { background-color: #111; padding: 10px; border-left: 3px solid #E20613; }
        div[data-testid="stMetricValue"] { color: #E20613 !important; }
    </style>""", unsafe_allow_html=True)

    # --- SIDEBAR (Spostata dentro la funzione per non apparire sempre) ---
    if os.path.exists("assets/logo_area199.png"): 
        st.sidebar.image("assets/logo_area199.png", use_container_width=True)
    
    st.sidebar.header("1. ANAGRAFICA")
    name = st.sidebar.text_input("Nome Cognome", "Mario Rossi")
    subject_type = st.sidebar.text_input("Attività / Sport", value="Sedentario")
    clinical_notes = st.sidebar.text_input("Note Cliniche / Stato", value="Nessuna", help="Scrivi liberamente (es. 'Infortunio Ginocchio SX'). L'AI leggerà questo campo.")
    
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

    # --- MAIN PAGE ---
    if st.session_state.get('analyzed'):
        d = st.session_state['data']
        d_sx = st.session_state.get('data_sx')
        
        st.title(f"ANALISI: {name}")
        st.caption(f"Ref: Dott. Petruzzi | Profilo: {subject_type} | Note: {clinical_notes}")
        
        t1, t2, t3 = st.tabs(["DATI", "GRAFICI", "REFERTO"])
        
        with t1:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("PhA", f"{d['PhA']}°")
            c2.metric("BF% (Grasso)", f"{d['FM_perc']}%") 
            c3.metric("SMM", f"{d['SMM_kg']} kg")
            c4.metric("TBW%", f"{d['TBW_perc']}%")
            st.divider()
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                st.markdown("#### Composizione Corporea")
                st.dataframe(pd.DataFrame({
                    "Parametro": ["Grasso (FM)", "Magro (FFM)", "Muscolo (SMM)", "Cellule (BCM)"],
                    "Valore (kg)": [d['FM_kg'], d['FFM_kg'], d['SMM_kg'], d['BCM_kg']]
                }), hide_index=True, use_container_width=True)
            with col_d2:
                st.markdown("#### Bilancio Idrico")
                st.dataframe(pd.DataFrame({
                    "Compartimento": ["Acqua Totale (TBW)", "Extra-Cellulare (ECW)", "Intra-Cellulare (ICW)"],
                    "Volume (L)": [d['TBW_L'], d['ECW_L'], d['ICW_L']]
                }), hide_index=True, use_container_width=True)

        with t2:
            if mode == "Bilateral (DX+SX)": c_g1, c_g2, c_g3 = st.columns([1, 1, 1])
            else: c_g1, c_g2 = st.columns(2)
                
            with c_g1:
                fig_biva, ax = plt.subplots(figsize=(4, 5))
                fig_biva.patch.set_facecolor('white'); ax.set_facecolor('white')
                ax.scatter(d['Rz']/(h/100), d['Xc']/(h/100), c='red', s=100, label="DX", edgecolor='black')
                if d_sx: ax.scatter(d_sx['Rz']/(h/100), d_sx['Xc']/(h/100), c='cyan', s=80, label="SX", edgecolor='black')
                ax.invert_yaxis(); ax.grid(color='#eee', linestyle='--'); 
                ax.spines['bottom'].set_color('black'); ax.spines['left'].set_color('black')
                ax.tick_params(colors='black', labelsize=8)
                ax.set_title("VETTORE BIVA (RXc)", fontsize=10, fontweight='bold', pad=10)
                ax.set_xlabel("R/H (Ohm/m)", fontsize=8); ax.set_ylabel("Xc/H (Ohm/m)", fontsize=8)
                ax.legend(fontsize=8)
                st.pyplot(fig_biva)
                
            with c_g2:
                fig_bars, ax2 = plt.subplots(figsize=(4, 5))
                fig_bars.patch.set_facecolor('white'); ax2.set_facecolor('white')
                bars = ax2.barh(['FM', 'SMM', 'BCM'], [d['FM_kg'], d['SMM_kg'], d['BCM_kg']], color=['#fca5a5', '#E20613', '#4ade80'])
                ax2.bar_label(bars, fmt='%.1f kg', padding=3, fontsize=8)
                ax2.set_title("COMPOSIZIONE (KG)", fontsize=10, fontweight='bold', pad=10)
                ax2.spines['bottom'].set_color('black'); ax2.spines['left'].set_color('black')
                ax2.tick_params(colors='black', labelsize=8)
                st.pyplot(fig_bars)
                
            if mode == "Bilateral (DX+SX)" and d_sx:
                with c_g3:
                    fig_body = draw_body_map(d['PhA'], d_sx['PhA'])
                    st.pyplot(fig_body)

        with t3:
            st.subheader("Referto Clinico (Direttore Scientifico)")
            if st.session_state.get('diagnosis'):
                st.text_area("Testo", st.session_state['diagnosis'], height=600)
            else:
                st.info("Clicca per generare il referto.")
            
            if st.button("ELABORA REFERTO COMPLETO"):
                with st.spinner("Analisi fisiologica profonda..."):
                    res = run_clinical_diagnosis(d, name, subject_type, gender, age, w, h, clinical_notes, d_sx)
                    st.session_state['diagnosis'] = res
                    st.rerun()

        st.markdown("---")
        c_s, c_p = st.columns(2)
        with c_s:
            if st.button("💾 ARCHIVIA"):
                try:
                    save_visit(name, w, rz, xc, d['PhA'], d['TBW_L'], d['FM_perc'], d['FFM_kg'])
                    st.success("OK")
                except: st.error("Errore DB")
        with c_p:
            try:
                biva_path = os.path.join(tempfile.gettempdir(), "biva.png")
                bars_path = os.path.join(tempfile.gettempdir(), "bars.png")
                fig_biva.savefig(biva_path, dpi=150, bbox_inches='tight')
                fig_bars.savefig(bars_path, dpi=150, bbox_inches='tight')
                
                body_path = None
                if mode == "Bilateral (DX+SX)" and d_sx and 'fig_body' in locals():
                    body_path = os.path.join(tempfile.gettempdir(), "body.png")
                    fig_body.savefig(body_path, dpi=150, bbox_inches='tight')
                
                pdf = BivaReportPDF(name)
                pdf_data = d.copy()
                pdf_data['Report_Text'] = st.session_state.get('diagnosis', "")
                pdf.generate_body(pdf_data, graph1_path=biva_path, graph2_path=bars_path, body_map_path=body_path)
                
                st.download_button("📄 SCARICA REFERTO PDF", bytes(pdf.output(dest='S')), f"Referto_{name}.pdf", "application/pdf")
            except Exception as e:
                st.error(f"Errore PDF: {e}")
