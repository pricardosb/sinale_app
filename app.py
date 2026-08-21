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

# --- TÍTULO FIXO DA APLICAÇÃO (TOPO) ---
st.markdown(
    "<div style='text-align: center; padding: 1.2rem; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; border-radius: 10px; margin-bottom: 1.5rem;'>"
    "<h1 style='margin:0;'>⚡ SINALE WEB</h1><p style='margin:0;'>Sistema de Remição de Pena no Serviço Público</p></div>",
    unsafe_allow_html=True
)

# --- BOTÃO DE RETORNO (EXIBIDO APENAS DENTRO DAS PÁGINAS) ---
if st.session_state["pagina"] != "menu":
    col_back, _ = st.columns([1, 4])
    with col_back:
        if st.button("⬅️ Voltar ao Menu Principal", use_container_width=True):
            st.session_state["pagina"] = "menu"
            st.rerun()
    st.markdown("---")

# --- CENTRAL DE OPÇÕES (MENU PRINCIPAL) ---
if st.session_state["pagina"] == "menu":
    st.markdown("### Selecione a operação desejada:")
    
    # Bloco 1: Funcionalidades Principais (1, 2 e 3)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 1. 📥 Inclusão")
        st.write("Integrar dados da origem diretamente na planilha do SINALE.")
        if st.button("Acessar Inclusão", key="btn_inc", use_container_width=True):
            st.session_state["pagina"] = "inclusao"
            st.rerun()

    with col2:
        st.warning("### 2. ✏️ Atualizações")
        st.write("Alterações em lote e cálculo automático de dias úteis.")
        if st.button("Acessar Atualizações", key="btn_atu", use_container_width=True):
            st.session_state["pagina"] = "atualizacoes"
            st.rerun()

    with col3:
        st.success("### 3. 🔍 Pesquisa")
        st.write("Consolidar múltiplos relatórios e emitir resumos Excel/Word.")
        if st.button("Acessar Pesquisa", key="btn_pesq", use_container_width=True):
            st.session_state["pagina"] = "pesquisa"
            st.rerun()

    st.markdown("---")

    # Bloco 2: Utilitários do Sistema (4 e 5)
    col4, col5 = st.columns(2)
    
    with col4:
        st.error("### 4. 🧹 Limpar Memória")
        st.write("Esvaziar planilhas e dados temporários carregados em sessão.")
        if st.button("Limpar Dados", key="btn_clean", use_container_width=True):
            st.session_state["wb_data"] = None
            st.session_state["source_df"] = None
            st.session_state["fila_modificacoes"] = []
            st.toast("Memória limpa com sucesso!", icon="✅")

    with col5:
        st.secondary = st.container()
        st.markdown("### 5. 🚪 Sair")
        st.write("Resetar todas as configurações e reiniciar o estado inicial.")
        if st.button("Encerrar Sessão", key="btn_exit", use_container_width=True):
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
