import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
import os
import tempfile
# Import dai moduli che abbiamo caricato al Passo 2
from modules.calculations import calculate_advanced_metrics
from modules.pdf_engine import BivaReportPDF
from modules.storage import save_visit

def run_biva_tool():
    st.header("ANALISI BIVA PRO")
    
    c1, c2 = st.columns(2)
    name = c1.text_input("Nome Cognome")
    gender = c2.selectbox("Sesso", ["M", "F"])
    
    c3, c4, c5, c6 = st.columns(4)
    age = c3.number_input("Età", 20)
    h = c4.number_input("Altezza cm", 175.0)
    w = c5.number_input("Peso kg", 75.0)
    
    st.subheader("Dati Elettrici")
    cc1, cc2 = st.columns(2)
    rz = cc1.number_input("Rz (Ohm)", 500)
    xc = cc2.number_input("Xc (Ohm)", 50)
    
    if st.button("CALCOLA DATI"):
        res = calculate_advanced_metrics(rz, xc, h, w, age, gender)
        
        # Mostra risultati
        k1, k2, k3 = st.columns(3)
        k1.metric("Angolo di Fase", f"{res['PhA']}°")
        k2.metric("Acqua Totale", f"{res['TBW_perc']}%")
        k3.metric("Massa Cellulare", f"{res['BCM_kg']} kg")
        
        # Grafico BIVA
        fig, ax = plt.subplots()
        ax.scatter(rz/(h/100), xc/(h/100), c='red', s=100)
        ax.set_title("Vettore BIVA")
        st.pyplot(fig)
        
        # Salvataggio e PDF
        if st.button("SALVA E GENERA PDF"):
            save_visit(name, w, rz, xc, res['PhA'], res['TBW_L'], res['FM_perc'], res['FFM_kg'])
            st.success("Dati Salvati!")
            # Qui andrebbe la generazione PDF completa
