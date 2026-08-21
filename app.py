import sys
from pathlib import Path

# Adiciona o diretório raiz ao PATH do Python
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
from paginas import inclusao, atualizacoes, pesquisa

st.set_page_config(page_title="SINALE WEB", layout="wide")

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

# --- BARRA DE NAVEGAÇÃO PRINCIPAL (SUBSTITUI O MENU LATERAL) ---
col_nav1, col_nav2, col_nav3, col_nav4, col_nav5, col_nav6 = st.columns(6)

with col_nav1:
    if st.button("🏠 Menu Principal", use_container_width=True):
        st.session_state["pagina"] = "menu"
        st.rerun()

with col_nav2:
    if st.button("📥 Inclusão", use_container_width=True):
        st.session_state["pagina"] = "inclusao"
        st.rerun()

with col_nav3:
    if st.button("✏️ Atualizações", use_container_width=True):
        st.session_state["pagina"] = "atualizacoes"
        st.rerun()

with col_nav4:
    if st.button("🔍 Pesquisa", use_container_width=True):
        st.session_state["pagina"] = "pesquisa"
        st.rerun()

with col_nav5:
    if st.button("🗑️ Limpar Arquivo", use_container_width=True):
        st.session_state["wb_data"] = None
        st.session_state["source_df"] = None
        st.session_state["fila_modificacoes"] = []
        st.toast("🧹 Memória limpa com sucesso!", icon="✅")

with col_nav6:
    if st.button("🚪 Sair", use_container_width=True):
        st.session_state.clear()
        st.session_state["pagina"] = "menu"
        st.rerun()

st.markdown("---")

# --- ROTEAMENTO DAS PÁGINAS ---
if st.session_state["pagina"] == "menu":
    st.markdown(
        "<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; border-radius: 12px; margin-bottom: 1.5rem;'>"
        "<h1>⚡ SINALE WEB</h1><p>Painel Geral de Operações</p></div>",
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 📥 Inclusão de Trabalho")
        st.write("Integrar dados da origem diretamente na planilha do SINALE.")
        if st.button("Acessar Inclusão", key="btn_card_inc", use_container_width=True):
            st.session_state["pagina"] = "inclusao"
            st.rerun()

    with col2:
        st.warning("### ✏️ Atualizações Gerais")
        st.write("Alterações gerais em lote e cálculo automático de dias úteis.")
        if st.button("Acessar Atualizações", key="btn_card_atu", use_container_width=True):
            st.session_state["pagina"] = "atualizacoes"
            st.rerun()

    with col3:
        st.success("### 🔍 Pesquisa para Remição")
        st.write("Consolidar múltiplos relatórios e emitir resumos Excel/Word.")
        if st.button("Acessar Pesquisa", key="btn_card_pesq", use_container_width=True):
            st.session_state["pagina"] = "pesquisa"
            st.rerun()

elif st.session_state["pagina"] == "inclusao":
    inclusao.renderizar()

elif st.session_state["pagina"] == "atualizacoes":
    atualizacoes.renderizar()

elif st.session_state["pagina"] == "pesquisa":
    pesquisa.renderizar()
