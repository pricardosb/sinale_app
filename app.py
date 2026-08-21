import sys
from pathlib import Path

# Adiciona o diretório raiz ao PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from paginas import inclusao, atualizacoes, pesquisa

st.set_page_config(page_title="SINALE WEB", layout="wide")

# --- BANDEIRA DA BAHIA AO FUNDO (MARCA D'ÁGUA SUAVE) ---
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(255, 255, 255, 0.88), rgba(255, 255, 255, 0.88)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/2/28/Bandeira_do_Estado_da_Bahia.svg") no-repeat center center fixed !important;
        background-size: cover !important;
    }
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

# --- TÍTULO FIXO DA APLICAÇÃO (TOPO) ---
st.markdown(
    "<div style='text-align: center; padding: 1.2rem; background-color: #1e3c72; color: white; border-radius: 10px; margin-bottom: 2rem;'>"
    "<h1 style='margin:0; font-size: 2.2rem;'>⚡ SINALE WEB</h1><p style='margin:0; opacity: 0.9;'>Sistema de Remição de Pena no Serviço Público</p></div>",
    unsafe_allow_html=True
)

# --- BOTÃO DE RETORNO (EXIBIDO APENAS DENTRO DAS PÁGINAS) ---
if st.session_state["pagina"] != "menu":
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ VOLTAR AO MENU", use_container_width=True):
            st.session_state["pagina"] = "menu"
            st.rerun()
    st.markdown("---")

# --- MENU PRINCIPAL ---
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

# --- CARREGAMENTO DAS PÁGINAS ---
elif st.session_state["pagina"] == "inclusao":
    inclusao.renderizar()

elif st.session_state["pagina"] == "atualizacoes":
    atualizacoes.renderizar()

elif st.session_state["pagina"] == "pesquisa":
    pesquisa.renderizar()
