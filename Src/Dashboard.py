import streamlit as st # pyright: ignore[reportMissingImports]
import requests
import os

# Page configuration
st.set_page_config(page_title="AI Home OS", page_icon="🤖")

# URLs de l'API (Backend)
API_BASE_URL = os.getenv("BACKEND_BASE_URL", "http://127.0.0.1:8000")
ASK_URL = f"{API_BASE_URL}/ask-agent"
CONFIRM_URL = f"{API_BASE_URL}/confirm-action"

st.title("🤖 AI Home OS")

# --- SIDEBAR : ACTIONS RAPIDES ---
with st.sidebar:
    st.header("⚡ Actions Agents")
    
    # Boutons correspondant aux outils de tes agents
    if st.button("📰 Revue de Presse"):
        st.session_state.pending_prompt = "Fais-moi une compilation des dernières actualités mondiales."

    if st.button("📅 Mon Calendrier"):
        st.session_state.pending_prompt = "Mon calendrier  ?"

    if st.button("📧 Résumé des Mails"):
        st.session_state.pending_prompt = "Peux-tu me résumer mes nouveaux emails ?"

    if st.button("🌤️ Météo Locale"):
        st.session_state.pending_prompt = "Quel temps fait-il aujourd'hui ?"

    st.divider()
    st.header("🏠 Scénarios Domotique")
    
    if st.button("🔌 Arrivée (Mode Nuit)"):
        st.session_state.pending_prompt = "Je suis rentré, allume le salon."
    
    if st.button("🛡️ Départ (Sécurité)"):
        st.session_state.pending_prompt = "Je pars, éteins toutes les lumières."

# --- INTERFACE DE CHAT ---
st.subheader("Control Center")
if "messages" not in st.session_state:
    st.session_state.messages = []

# Affichage de l'historique
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Gestion des prompts venant des boutons de la sidebar
prompt = st.chat_input("How can I help you today?")
if "pending_prompt" in st.session_state:
    prompt = st.session_state.pending_prompt
    del st.session_state.pending_prompt

# Logique d'envoi
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        # Appel à l'API FastAPI
        response = requests.post(ASK_URL, json={"instruction": prompt})
        data = response.json()
        
        api_response = data.get('response', "No response from server.")
        api_details = data.get('details', [])
        needs_val = data.get('needs_validation', False)
        action_details = data.get('action_details', {})

        full_response = f"{api_response}\n\n**System Logs:** {', '.join(api_details) if api_details else 'None'}"

        with st.chat_message("assistant"):
            st.markdown(api_response)
            
            # --- INTERFACE DE VALIDATION HUMAINE ---
            if needs_val:
                st.info(f"🛡️ **Action en attente :** `{action_details}`")
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("✅ Confirmer", key="btn_confirm"):
                        res_confirm = requests.post(CONFIRM_URL)
                        st.success(res_confirm.json().get("response"))
                
                with col2:
                    if st.button("❌ Annuler", key="btn_cancel"):
                        st.error("Action annulée.")
            
            st.caption(f"Logs: {', '.join(api_details)}")

        st.session_state.messages.append({"role": "assistant", "content": full_response})

    except Exception as e:
        error_msg = f"⚠️ Connection error: {str(e)}"
        st.error(error_msg)