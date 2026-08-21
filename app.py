import sys
from pathlib import Path

# Adiciona o diretório raiz ao PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from paginas import inclusao, atualizacoes, pesquisa

st.set_page_config(page_title="SINALE WEB", layout="wide")

# --- ESTILIZAÇÃO CSS DEDICADA PARA CADA BOTÃO ---
st.markdown("""
<style>
    /* Estilo Base Geral dos Botões */
    div.stButton > button {
        width: 100%;
        height: 75px;
        font-size: 15px !important;
        font-weight: 700 !important;
        letter-spacing: 0.8px;
        border-radius: 10px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        transition: all 0.25s ease-in-out !important;
        text-transform: uppercase;
        color: white !important;
    }

    /* Efeito de Elevação ao Passar o Mouse (Hover) */
    div.stButton > button:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 22px rgba(0, 0, 0, 0.25);
        filter: brightness(1.12);
    }

    /* Efeito ao Clicar */
    div.stButton > button:active {
        transform: translateY(1px);
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }

    /* 1. Inclusão: Azul */
    .btn-inclusao div.stButton > button {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
    }

    /* 2. Atualização: Laranja/Âmbar */
    .btn-atualizacao div.stButton > button {
        background: linear-gradient(135deg, #d97706 0%, #b45309 100%) !important;
    }

    /* 3. Pesquisa: Verde Esmeralda */
    .btn-pesquisa div.stButton > button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
    }

    /* 4. Limpar Memória: Vermelho */
    .btn-limpar div.stButton > button {
        background: linear-gradient(135deg, #dc2626 0%, #991b1b 100%) !important;
    }

    /* 5. Sair: Grafite */
    .btn-sair div.stButton > button {
        background: linear-gradient(135deg, #4b5563 0%, #1f2937 100%) !important;
    }

    /* Botão Voltar (Compacto) */
    .btn-voltar div.stButton > button {
        height: 45px !important;
        font-size: 13px !important;
        background: linear-gradient(135deg, #374151 0%, #111827 100%) !important;
    }
</style>
""", unsafe_allow_html=True)

# Inicializações Globais de Estado
if "source_df" not in st.session_state:
    st.session_state["source_df"] = None
if "wb_data" not in st.session_state:
    st.session_state["wb_data"] = None
if "last_dest_name" not in st.session_state:
    st.session_state["last_dest_name"] = None
if "fila_modificacoes" not in st.session_state:
    st.session_state["fila_modificacoes"] = []
if "select_all" not in st.session_state:
    st.session_state["select_all"] = False
if "file_settings" not in st.session_state:
    st.session_state["file_settings"] = {}
if "pesquisa_df" not in st.session_state:
    st.session_state["pesquisa_df"] = None
if "executar_config" not in st.session_state:
    st.session_state["executar_config"] = False
if "pagina" not in st.session_state:
    st.session_state["pagina"] = "menu"

# --- TÍTULO FIXO DA APLICAÇÃO (TOPO) ---
st.markdown(
    "<div style='text-align: center; padding: 1.2rem; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; border-radius: 10px; margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.15);'>"
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

# --- MENU PRINCIPAL COM CORES EXCLUSIVAS ---
if st.session_state["pagina"] == "menu":
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

    st.markdown("<br>", unsafe_allow_html=True)

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
