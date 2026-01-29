import streamlit as st
from modules import coaching_app, biva_app # Nota: se bikefit è pronto, importa anche quello

st.set_page_config(page_title="AREA 199 HUB", layout="wide", page_icon="🔴")

# --- LOGIN ---
if 'role' not in st.session_state:
    st.session_state['role'] = None

if st.session_state['role'] is None:
    st.title("AREA 199 PERFORMANCE HUB")
    st.info("Portale Unificato Dott. Petruzzi")
    
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("ATLETA")
        email = st.text_input("La tua email")
        if st.button("ENTRA"):
            if "@" in email:
                st.session_state['role'] = 'athlete'
                st.session_state['email'] = email
                st.rerun()
    
    with c2:
        st.subheader("STAFF")
        pwd = st.text_input("Password", type="password")
        if st.button("LOGIN ADMIN"):
            if pwd == "PETRUZZI199":
                st.session_state['role'] = 'admin'
                st.rerun()
            else:
                st.error("Password errata")

# --- ATLETA ---
elif st.session_state['role'] == 'athlete':
    if st.sidebar.button("ESCI"):
        st.session_state['role'] = None
        st.rerun()
    coaching_app.run_athlete_dashboard(st.session_state['email'])

# --- ADMIN ---
elif st.session_state['role'] == 'admin':
    st.sidebar.title("PANNELLO DI CONTROLLO")
    app_choice = st.sidebar.radio("SCEGLI TOOL", ["COACHING MANAGER", "LAB BIVA"])
    
    if st.sidebar.button("LOGOUT"):
        st.session_state['role'] = None
        st.rerun()
        
    if app_choice == "COACHING MANAGER":
        coaching_app.run_coach_dashboard()
        
    elif app_choice == "LAB BIVA":
        # Questo lancerà il codice ESATTO della tua BIA
        biva_app.run_biva()
