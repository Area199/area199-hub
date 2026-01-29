import streamlit as st
import os
# Importiamo i nostri nuovi moduli app
from modules import coaching_app, biva_app

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="AREA 199 | HUB", layout="wide", page_icon="🔴")

# --- CSS ---
st.markdown("""
<style>
    .stApp {background-color: #000000; color: #ffffff;}
    h1, h2, h3 {color: #E20613 !important;}
    .stButton>button {border: 2px solid #E20613; color: #E20613; background: transparent; width: 100%; font-weight: bold;}
    .stButton>button:hover {background: #E20613; color: white;}
</style>
""", unsafe_allow_html=True)

# --- LOGO ---
if os.path.exists("logo_dark.jpg"):
    st.sidebar.image("logo_dark.jpg", use_container_width=True)

# --- SISTEMA DI LOGIN ---
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None

# SE NON SEI LOGGATO
if st.session_state['user_role'] is None:
    st.title("AREA 199 PERFORMANCE HUB")
    st.info("Benvenuto nel portale ufficiale.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("ACCESSO ATLETI")
        email = st.text_input("Inserisci la tua Email")
        if st.button("ENTRA COME ATLETA"):
            if "@" in email: # Controllo base, poi coaching_app controllerà se esiste
                st.session_state['user_role'] = 'athlete'
                st.session_state['user_email'] = email
                st.rerun()
            else:
                st.error("Email non valida")
                
    with col2:
        st.subheader("ACCESSO STAFF")
        pwd = st.text_input("Password Admin", type="password")
        if st.button("ENTRA COME ADMIN"):
            if pwd == "PETRUZZI199":
                st.session_state['user_role'] = 'admin'
                st.rerun()
            else:
                st.error("Password Errata")

# SE SEI UN ATLETA
elif st.session_state['user_role'] == 'athlete':
    if st.sidebar.button("ESCI"):
        st.session_state['user_role'] = None
        st.rerun()
    
    # Chiama il modulo Coaching in modalità Atleta
    coaching_app.run_athlete_dashboard(st.session_state['user_email'])

# SE SEI L'ADMIN (TU)
elif st.session_state['user_role'] == 'admin':
    st.sidebar.title("PANNELLO CONTROLLO")
    
    app_mode = st.sidebar.radio("SCEGLI TOOL", ["1. GESTIONE COACHING", "2. LAB BIVA", "3. LAB BIOMECCANICO"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state['user_role'] = None
        st.rerun()

    if app_mode == "1. GESTIONE COACHING":
        coaching_app.run_coach_dashboard()
        
    elif app_mode == "2. LAB BIVA":
        biva_app.run_biva_tool()
        
    elif app_mode == "3. LAB BIOMECCANICO":
        st.title("BIKEFIT LAB")
        st.info("Qui caricheremo il modulo video (Step successivo)")
