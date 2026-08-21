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

# Menu Lateral de Roteamento Rápido
st.sidebar.title("📌 Menu de Opções")
opcao = st.sidebar.radio(
    "Navegação:",
    [
        "Menu Principal",
        "INCLUSÃO DE TRABALHO",
        "ATUALIZAÇÕES GERAIS",
        "PESQUISA PARA REMIÇÃO",
        "LIMPAR ARQUIVO",
        "SAIR DO SISTEMA"
    ]
)

if opcao == "INCLUSÃO DE TRABALHO":
    st.session_state["pagina"] = "inclusao"
elif opcao == "ATUALIZAÇÕES GERAIS":
    st.session_state["pagina"] = "atualizacoes"
elif opcao == "PESQUISA PARA REMIÇÃO":
    st.session_state["pagina"] = "pesquisa"
elif opcao == "LIMPAR ARQUIVO":
    st.session_state["wb_data"] = None
    st.session_state["source_df"] = None
    st.session_state["fila_modificacoes"] = []
    st.sidebar.success("Dados da memória limpos com sucesso!")
elif opcao == "SAIR DO SISTEMA":
    st.session_state.clear()
    st.session_state["pagina"] = "menu"
    st.rerun()

# --- TELA DO MENU PRINCIPAL ---
if st.session_state["pagina"] == "menu":
    st.markdown(
        "<div style='text-align: center; padding: 1.5rem; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); color: white; border-radius: 12px; margin-bottom: 1.5rem;'>"
        "<h1>⚡ SINALE WEB</h1><p>Painel Geral de Operações</p></div>",
        unsafe_allow_html=True
    )
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.info("### 📥 Inclusão")
        st.write("Integrar dados da origem diretamente na planilha do SINALE.")
        if st.button("Acessar Inclusão", use_container_width=True):
            st.session_state["pagina"] = "inclusao"
            st.rerun()

    with col2:
        st.warning("### ✏️ Atualizações")
        st.write("Alterações gerais em lote e cálculo automático de dias úteis.")
        if st.button("Acessar Atualizações", use_container_width=True):
            st.session_state["pagina"] = "atualizacoes"
            st.rerun()

    with col3:
        st.success("### 🔍 Pesquisa Remição")
        st.write("Consolidar múltiplos relatórios e emitir resumos Excel/Word.")
        if st.button("Acessar Pesquisa", use_container_width=True):
            st.session_state["pagina"] = "pesquisa"
            st.rerun()

# --- ROTEAMENTO DOS MÓDULOS ---
elif st.session_state["pagina"] == "inclusao":
    inclusao.renderizar()

elif st.session_state["pagina"] == "atualizacoes":
    atualizacoes.renderizar()

elif st.session_state["pagina"] == "pesquisa":
    pesquisa.renderizar()
