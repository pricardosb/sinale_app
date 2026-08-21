import sys
from pathlib import Path

# Adiciona o diretório raiz ao PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from paginas import inclusao, atualizacoes, pesquisa

st.set_page_config(page_title="SINALE WEB", layout="wide")

# --- ESTILIZAÇÃO CSS CORRIGIDA PARA VISIBILIDADE DO TEXTO ---
st.markdown("""
<style>
    /* Estilo Base dos Botões */
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        border-radius: 8px !important;
        border: none !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.12) !important;
        transition: all 0.2s ease-in-out !important;
    }

    /* FORÇA O TEXTO INTERNO DO STREAMLIT (TAGS P E SPAN) A FICAR VISÍVEL E BRANCO */
    div.stButton > button *, 
    div.stButton > button p, 
    div.stButton > button span {
        color: #FFFFFF !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* Efeito Hover */
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25) !important;
    }

    /* CORES INDIVIDUAIS POR CLASSE */
    .btn-inclusao div.stButton > button { background-color: #1d4ed8 !important; }
    .btn-atualizacao div.stButton > button { background-color: #d97706 !important; }
    .btn-pesquisa div.stButton > button { background-color: #15803d !important; }
    .btn-limpar div.stButton > button { background-color: #dc2626 !important; }
    .btn-sair div.stButton > button { background-color: #4b5563 !important; }

    /* Botão Voltar (Página interna) */
    .btn-voltar div.stButton > button { 
        background-color: #374151 !important; 
        height: 45px !important; 
    }
    .btn-voltar div.stButton > button * {
        font-size: 13px !important;
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
    "<div style='text-align: center; padding: 1.2rem; background-color: #1e3c72; color: white; border-radius: 10px; margin-bottom: 1.5rem; box-shadow: 0 4px 10px rgba(0,0,0,0.1);'>"
    "<h1 style='margin:0; font-size: 2.2rem;'>⚡ SINALE WEB</h1><p style='margin:0; opacity: 0.9;'>Sistema de Remição de Pena no Serviço Público</p></div>",
    unsafe_allow_html=True
)

# --- BOTÃO DE RETORNO (EXIBIDO APENAS DENTRO DAS PÁGINAS) ---
if st.session_state["pagina"] != "menu":
    col_back, _ = st.columns([1, 4])
    with col_back:
        st.markdown('<div class="btn-voltar">', unsafe_allow_html=True)
        if st.button("⬅️ VOLTAR AO MENU", use_container_width=True):
            st.session_state["pagina"] = "menu"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("---")

# --- MENU PRINCIPAL ---
if st.session_state["pagina"] == "menu":
    st.markdown("### Selecione a operação desejada:")
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="btn-inclusao">', unsafe_allow_html=True)
        if st.button("INCLUSÃO PARA TRABALHO", key="btn_inc", use_container_width=True):
            st.session_state["pagina"] = "inclusao"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="btn-atualizacao">', unsafe_allow_html=True)
        if st.button("ATUALIZAÇÃO GERAL", key="btn_atu", use_container_width=True):
            st.session_state["pagina"] = "atualizacoes"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="btn-pesquisa">', unsafe_allow_html=True)
        if st.button("PESQUISA REMIÇÃO", key="btn_pesq", use_container_width=True):
            st.session_state["pagina"] = "pesquisa"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="btn-limpar">', unsafe_allow_html=True)
        if st.button("LIMPAR MEMÓRIA", key="btn_clean", use_container_width=True):
            st.session_state["wb_data"] = None
            st.session_state["source_df"] = None
            st.session_state["fila_modificacoes"] = []
            st.toast("Memória limpa com sucesso!", icon="✅")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="btn-sair">', unsafe_allow_html=True)
        if st.button("SAIR", key="btn_exit", use_container_width=True):
            st.session_state.clear()
            st.session_state["pagina"] = "menu"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# --- CARREGAMENTO DAS PÁGINAS ---
elif st.session_state["pagina"] == "inclusao":
    inclusao.renderizar()

elif st.session_state["pagina"] == "atualizacoes":
    atualizacoes.renderizar()

elif st.session_state["pagina"] == "pesquisa":
    pesquisa.renderizar()
