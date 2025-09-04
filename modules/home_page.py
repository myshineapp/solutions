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
    
    # Adicionando estilo CSS para as caixas de links
    st.markdown("""
        <style>
            .link-container {
                background-color: #f65a93;
                border-radius: 5px;
                padding: 10px;
                margin-bottom: 10px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
            }
            .link-container a {
                color: white;
                text-decoration: none;
                font-size: 1.2rem;
                font-weight: bold;
                display: block;
                text-align: center;
            }
            .link-container a:hover {
                text-decoration: underline;
            }
        </style>
    """, unsafe_allow_html=True)
    
    st.header("Acessos Rápidos")
    
    # Inicializa o estado da sessão com os links salvos
    if 'links' not in st.session_state:
        st.session_state.links = load_links()

    if st.session_state.links:
        for link_data in st.session_state.links:
            with st.container():
                st.markdown(f'<div class="link-container"><a href="{link_data["url"]}" target="_blank">{link_data["title"]}</a></div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum link adicionado ainda.")
