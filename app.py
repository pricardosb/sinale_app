import sys
from pathlib import Path

# Adiciona o diretório raiz ao PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from paginas import inclusao, atualizacoes, pesquisa

st.set_page_config(page_title="SINALE WEB", layout="wide")

# --- BANDEIRA DA BAHIA AO FUNDO E BOTOES EM AZUL, VERMELHO E BRANCO ---
st.markdown("""
<style>
    /* Marca d'água da Bandeira da Bahia no Fundo */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(245, 247, 250, 0.90), rgba(245, 247, 250, 0.90)), 
                    url("https://upload.wikimedia.org/wikipedia/commons/2/28/Bandeira_do_Estado_da_Bahia.svg") no-repeat center center fixed !important;
        background-size: cover !important;
    }

    /* Estilo Base dos Botões */
    div.stButton > button {
        width: 100% !important;
        height: 70px !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.2s ease-in-out !important;
    }

    div.stButton > button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 18px rgba(0, 0, 0, 0.25) !important;
    }

    /* 1. Botão Azul (Texto Branco) */
    .btn-azul div.stButton > button {
        background-color: #002B7F !important;
        border: none !important;
    }
    .btn-azul div.stButton > button * {
        color: #FFFFFF !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* 2. Botão Vermelho (Texto Branco) */
    .btn-vermelho div.stButton > button {
        background-color: #CE1126 !important;
        border: none !important;
    }
    .btn-vermelho div.stButton > button * {
        color: #FFFFFF !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* 3. Botão Branco (Borda e Texto Azul) */
    .btn-branco div.stButton > button {
        background-color: #FFFFFF !important;
        border: 2px solid #002B7F !important;
    }
    .btn-branco div.stButton > button * {
        color: #002B7F !important;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
    }

    /* Botão Voltar (Páginas Internas) */
    .btn-voltar div.stButton > button {
        height: 48px !important;
        background-color: #FFFFFF !important;
        border: 2px solid #CE1126 !important;
    }
    .btn-voltar div.stButton > button * {
        color: #CE1126 !important;
        font-size: 13px !important;
        font-weight: 700 !important;
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

# --- TÍTULO FIXO DA APLICAÇÃO (AZUL BAHIA COM BORDA VERMELHA) ---
st.markdown(
    "<div style='text-align: center; padding: 1.2rem; background-color: #002B7F; color: white; border-radius: 10px; border-bottom: 5px solid #CE1126; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);'>"
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

# --- MENU PRINCIPAL (COMBINAÇÃO AZUL, VERMELHO E BRANCO) ---
if st.session_state["pagina"] == "menu":
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="btn-azul">', unsafe_allow_html=True)
        if st.button("INCLUSÃO PARA TRABALHO", key="btn_inc", use_container_width=True):
            st.session_state["pagina"] = "inclusao"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="btn-vermelho">', unsafe_allow_html=True)
        if st.button("ATUALIZAÇÃO GERAL", key="btn_atu", use_container_width=True):
            st.session_state["pagina"] = "atualizacoes"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col3:
        st.markdown('<div class="btn-branco">', unsafe_allow_html=True)
        if st.button("PESQUISA REMIÇÃO", key="btn_pesq", use_container_width=True):
            st.session_state["pagina"] = "pesquisa"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

    col4, col5 = st.columns(2)
    with col4:
        st.markdown('<div class="btn-vermelho">', unsafe_allow_html=True)
        if st.button("LIMPAR MEMÓRIA", key="btn_clean", use_container_width=True):
            st.session_state["wb_data"] = None
            st.session_state["source_df"] = None
            st.session_state["fila_modificacoes"] = []
            st.toast("Memória limpa com sucesso!", icon="✅")
        st.markdown('</div>', unsafe_allow_html=True)

    with col5:
        st.markdown('<div class="btn-azul">', unsafe_allow_html=True)
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
