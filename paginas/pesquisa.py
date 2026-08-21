import io
import requests
import pandas as pd
import streamlit as st

# --- FUNÇÕES DE INTEGRAÇÃO COM O ONEDRIVE (MICROSOFT GRAPH API) ---

def obter_token_onedrive():
    """Obtém o token de acesso OAuth2 usando as credenciais do st.secrets."""
    try:
        cfg = st.secrets["onedrive"]
        url = f"https://login.microsoftonline.com/{cfg['tenant_id']}/oauth2/v2.0/token"
        data = {
            "client_id": cfg["client_id"],
            "scope": "https://graph.microsoft.com/.default",
            "client_secret": cfg["client_secret"],
            "grant_type": "client_credentials"
        }
        response = requests.post(url, data=data, timeout=10)
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception:
        return None
    return None


def listar_arquivos_nuvem(pasta="SINALE_WEB"):
    """Lista todos os arquivos Excel (.xlsx / .xls) presentes na pasta definida do OneDrive."""
    token = obter_token_onedrive()
    if not token:
        return []

    try:
        user_id = st.secrets["onedrive"]["user_id"]
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://graph.microsoft.com/v1.0/users/{user_id}/drive/root:/{pasta}:/children"

        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            itens = response.json().get("value", [])
            # Filtra apenas arquivos Excel
            return [
                {
                    "nome": item["name"],
                    "id": item["id"],
                    "download_url": item.get("@microsoft.graph.downloadUrl")
                }
                for item in itens if item["name"].lower().endswith(('.xlsx', '.xls'))
            ]
    except Exception as e:
        st.error(f"Erro ao acessar pasta na nuvem: {e}")
    return []


@st.cache_data(ttl=300, show_spinner=False)
def carregar_planilha_nuvem(download_url):
    """Baixa e converte o arquivo do OneDrive diretamente para um DataFrame Pandas."""
    try:
        response = requests.get(download_url, timeout=15)
        if response.status_code == 200:
            return pd.read_excel(io.BytesIO(response.content))
    except Exception as e:
        st.error(f"Erro ao ler arquivo da nuvem: {e}")
    return None


# --- INTERFACE DA PÁGINA DE PESQUISA ---

def renderizar():
    st.subheader("🔍 Pesquisa e Consulta de Remição de Pena")
    st.markdown("Consulte relatórios e históricos de remição armazenados na nuvem (OneDrive).")

    # Verifica se os segredos do OneDrive foram configurados
    if "onedrive" not in st.secrets:
        st.warning("⚠️ As credenciais do OneDrive ainda não foram configuradas em `.streamlit/secrets.toml`.")
        st.info("Para testar localmente antes de conectar a API, use a caixa de upload manual abaixo:")
        
        uploaded_file = st.file_uploader("Carregar planilha local para teste", type=["xlsx", "xls"])
        if uploaded_file:
            df = pd.read_excel(uploaded_file)
            exibir_interface_pesquisa(df, uploaded_file.name)
        return

    # Nome da pasta configurada ou padrão
    nome_pasta = st.secrets["onedrive"].get("pasta_destino", "SINALE_WEB")

    with st.spinner("Conectando ao OneDrive e buscando arquivos..."):
        arquivos_nuvem = listar_arquivos_nuvem(pasta=nome_pasta)

    if not arquivos_nuvem:
        st.error(f"Nenhum arquivo Excel encontrado na pasta **'{nome_pasta}'** do OneDrive ou erro de conexão.")
        if st.button("🔄 Tentar Novamente"):
            st.rerun()
        return

    # Seleção do arquivo da nuvem
    opcoes_arquivos = {arq["nome"]: arq for arq in arquivos_nuvem}
    
    col_sel, col_ref = st.columns([3, 1])
    with col_sel:
        arquivo_selecionado = st.selectbox(
            "📁 Selecione o arquivo na nuvem para consulta:",
            options=list(opcoes_arquivos.keys())
        )
    with col_ref:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if arquivo_selecionado:
        dados_arquivo = opcoes_arquivos[arquivo_selecionado]
        
        with st.spinner(f"Carregando **{arquivo_selecionado}**..."):
            df = carregar_planilha_nuvem(dados_arquivo["download_url"])

        if df is not None and not df.empty:
            exibir_interface_pesquisa(df, arquivo_selecionado)
        else:
            st.warning("O arquivo selecionado está vazio ou não pôde ser lido.")


def exibir_interface_pesquisa(df: pd.DataFrame, nome_arquivo: str):
    """Renderiza os filtros e a tabela de dados pesquisada."""
    st.success(f"Planilha **{nome_arquivo}** carregada ({len(df)} registros).", icon="📊")

    st.markdown("---")
    
    # Campo de Busca Geral
    termo_busca = st.text_input("🔎 Digite para pesquisar (Nome, CPF, Matrícula, Processo, etc.):", "")

    # Filtro dinâmico
    if termo_busca:
        # Filtra em todas as colunas de texto
        mascara = df.astype(str).apply(
            lambda col: col.str.contains(termo_busca, case=False, na=False)
        ).any(axis=1)
        df_filtrado = df[mascara]
    else:
        df_filtrado = df

    # Exibição dos resultados
    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Total de Registros Encontrados", len(df_filtrado))
    
    # Tenta somar a coluna de dias remidos se existir
    colunas_dias = [c for c in df_filtrado.columns if "dia" in c.lower() or "remi" in c.lower()]
    if colunas_dias:
        col_dias = colunas_dias[0]
        total_dias = pd.to_numeric(df_filtrado[col_dias], errors='coerce').sum()
        col_m2.metric(f"Total de {col_dias}", f"{int(total_dias) if pd.notnull(total_dias) else 0} dias")

    # Tabela Interativa
    st.dataframe(
        df_filtrado,
        use_container_width=True,
        hide_index=True
    )
