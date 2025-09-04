import streamlit as st
import json
import os
import re

# Nome do arquivo para salvar os dados
LINKS_FILE = "acessos_rapidos.json"

def load_links():
    """Carrega os links salvos do arquivo JSON."""
    if os.path.exists(LINKS_FILE):
        try:
            with open(LINKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    return []

def home_page():
    """Renderiza a página inicial com o mural de botões."""
    st.title("Seja bem vindo, Brother N' Shine!")
    st.markdown("---")
    
    # Adicionando estilo CSS para os botões do mural
    st.markdown("""
        <style>
            .stButton > button.mural-button {
                background: #f65a93 !important;
                color: white !important;
                border: 1px solid #f65a93 !important;
                width: 100%; /* Garante que o botão ocupe a largura total */
                margin-bottom: 5px; /* Adiciona um pequeno espaçamento entre os botões */
            }
            .stButton > button.mural-button:hover {
                background: #f770a3 !important; /* Cor um pouco mais clara no hover */
            }
            .stButton > button.mural-button:active,
            .stButton > button.mural-button:focus,
            .stButton > button.mural-button:checked {
                background: #f65a93 !important;
                color: white !important;
            }
            /* Estilo para remover a borda e padding do container do botão para melhor alinhamento */
            div[data-testid="column"] {
                padding-left: 0 !important;
                padding-right: 0 !important;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.header("Acessos Rápidos")
    
    # Inicializa o estado da sessão com os links salvos
    if 'links' not in st.session_state:
        st.session_state.links = load_links()

    if st.session_state.links:
        for link_data in st.session_state.links:
            st.markdown(
                f'<a href="{link_data["url"]}" target="_blank" style="text-decoration: none;">'
                f'<button class="mural-button">{link_data["title"]}</button>'
                f'</a>',
                unsafe_allow_html=True
            )
    else:
        st.info("Nenhum link adicionado ainda.")