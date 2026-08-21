import sys
from pathlib import Path

# Adiciona o diretório raiz ao PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from paginas import inclusao, atualizacoes, pesquisa

st.set_page_config(page_title="SINALE WEB", layout="wide")

# --- BANDEIRA DA BAHIA EM SVG INLINE (MARCA D'ÁGUA) ---
BAHIA_FLAG_SVG = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 900 600'><rect width='900' height='600' fill='%23ffffff'/><rect y='150' width='900' height='150' fill='%23c8102e'/><rect y='450' width='900' height='150' fill='%23c8102e'/><rect width='300' height='300' fill='%23002b7f'/><polygon points='150,60 225,225 75,225' fill='%23ffffff'/></svg>"

st.markdown(f"""
<style>
    /* Marca d'água de fundo */
    .stApp {{
        background-image: linear-gradient(rgba(255, 255, 255, 0.90), rgba(255, 255, 255, 0.90)), 
                          url("{BAHIA_FLAG_SVG}") !important;
        background-repeat: repeat !important;
        background-position: top left !important;
        background-size: 300px 200px !important;
        background-attachment: fixed !important;
    }}

    [data-testid="stAppViewContainer"],
    [data-testid="stHeader"],
    [data-testid="stMain"],
    .main {{
        background: transparent !important;
    }}

    /* Botão Voltar Fixo/Sticky (Sempre visível abaixo do título durante a rolagem) */
    .sticky-back-container {{
        position: sticky;
        top: 2.8rem;
        z-index: 999;
        background-color: rgba(255, 255, 255, 0.95);
        padding: 10px 0;
        border-bottom: 2px solid #e5e7eb;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(4px);
    }}
</style>
""", unsafe_allow_html=True)

# Inicializações Globais de Estado
if "source_df" not in st.session_state:
    st.session_state["source_df"] = None
if "wb_data" not in st.session_state:
    st.session_state["wb_data"] = None
if "fila_modificacoes" not in st.session_state:
    st.session_state["fila_modificacoes"] = []
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "menu"

# --- TÍTULO FIXO NO TOPO DE TODAS AS PÁGINAS ---
st.markdown(
    "<div style='text-align: center; padding: 1.2rem; background-color: #1e3c72; color: white; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 4px 10px rgba(0,0,0,0.15);'>"
    "<h1 style='margin:0; font-size: 2.2rem;'>⚡ SINALE WEB</h1><p style='margin:0; opacity: 0.9;'>Sistema de Remição de Pena no Serviço Público</p></div>",
    unsafe_allow_html=True
)

# --- BOTÃO VOLTAR (ABAIXO DO TÍTULO E STICKY/VISÍVEL AO ROLAR) ---
if st.session_state["pagina"] != "menu":
    st.markdown('<div class="sticky-back-container">', unsafe_allow_html=True)
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ VOLTAR AO MENU", use_container_width=True):
            st.session_state["pagina"] = "menu"
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# --- ROTEAMENTO DE PÁGINAS ---
if st.session_state["pagina"] == "menu":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("INCLUSÃO PARA TRABALHO", key="btn_inc", use_container_width=True):
            st.session_state["pagina"] = "inclusao"
            st.rerun()

    with col2:
        if st.button("ATUALIZAÇÃO GERAL", key="btn_atu", use_container_width=True):
            st.session_state["pagina"] = "atualizacoes"
            st.rerun()

    with col3:
        if st.button("PESQUISA REMIÇÃO", key="btn_pesq", use_container_width=True):
            st.session_state["pagina"] = "pesquisa"
            st.rerun()

    st.markdown("<br><br>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)
    with col4:
        if st.button("LIMPAR MEMÓRIA", key="btn_clean", use_container_width=True):
            st.session_state["wb_data"] = None
            st.session_state["source_df"] = None
            st.session_state["fila_modificacoes"] = []
            st.toast("Memória limpa com sucesso!", icon="✅")

    with col5:
        if st.button("SAIR", key="btn_exit", use_container_width=True):
            st.session_state.clear()
            st.session_state["pagina"] = "menu"
            st.rerun()

elif st.session_state["pagina"] == "inclusao":
    inclusao.renderizar()

elif st.session_state["pagina"] == "atualizacoes":
    atualizacoes.renderizar()

elif st.session_state["pagina"] == "pesquisa":
    pesquisa.renderizar()
