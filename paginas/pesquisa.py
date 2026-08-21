import io
import pandas as pd
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


def conectar_google_drive():
    """Autentica na API do Google Drive usando as credenciais do Secrets."""
    try:
        if "gcp_service_account" not in st.secrets:
            return None
        
        creds_dict = dict(st.secrets["gcp_service_account"])
        # Ajusta a quebra de linha da private_key caso venha formatada
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"Erro ao conectar com Google Drive: {e}")
        return None


def listar_arquivos_drive(folder_id):
    """Lista todos os arquivos Excel e Google Sheets dentro da pasta configurada."""
    service = conectar_google_drive()
    if not service:
        return []

    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)"
        ).execute()

        itens = results.get("files", [])
        
        # Filtra apenas planilhas (.xlsx, .xls e Google Sheets)
        return [
            item for item in itens 
            if item["name"].lower().endswith(('.xlsx', '.xls')) 
            or item["mimeType"] == "application/vnd.google-apps.spreadsheet"
        ]
    except Exception as e:
        st.error(f"Erro ao listar arquivos do Google Drive: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def carregar_planilha_drive(file_id, mime_type):
    """Baixa a planilha da nuvem e carrega como DataFrame Pandas."""
    service = conectar_google_drive()
    if not service:
        return None

    try:
        # Se for Google Sheets nativo, exporta como .xlsx
        if mime_type == "application/vnd.google-apps.spreadsheet":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        return pd.read_excel(fh)
    except Exception as e:
        st.error(f"Erro ao carregar a planilha da nuvem: {e}")
        return None


def renderizar():
    st.subheader("🔍 Pesquisa e Consulta de Remição de Pena")
    st.markdown("Consulte relatórios e históricos armazenados na pasta do **Google Drive**.")

    # 1. Verifica credenciais
    if "gcp_service_account" not in st.secrets:
        st.error("❌ As credenciais do Google Drive não foram encontradas no `st.secrets`.")
        st.info("Adicione o bloco `[gcp_service_account]` com suas chaves nas configurações do Streamlit.")
        return

    # 2. Obtém o ID da pasta
    folder_id = st.secrets["gcp_service_account"].get("pasta_id")
    if not folder_id:
        st.error("❌ O parâmetro `pasta_id` não foi configurado em `[gcp_service_account]` no Secrets.")
        return

    # 3. Busca os arquivos na nuvem
    with st.spinner("Conectando ao Google Drive e buscando planilhas..."):
        arquivos = listar_arquivos_drive(folder_id)

    if not arquivos:
        st.warning("Nenhuma planilha Excel ou Google Sheets foi encontrada na pasta configurada.")
        if st.button("🔄 Tentar Novamente"):
            st.rerun()
        return

    # 4. Seleção da planilha
    opcoes = {arq["name"]: arq for arq in arquivos}

    col_sel, col_ref = st.columns([3, 1])
    with col_sel:
        arquivo_selecionado = st.selectbox(
            "📁 Escolha a planilha no Google Drive para consulta:",
            options=list(opcoes.keys())
        )
    with col_ref:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 5. Exibição dos dados
    if arquivo_selecionado:
        dados = opcoes[arquivo_selecionado]
        with st.spinner(f"Lendo **{arquivo_selecionado}** do Google Drive..."):
            df = carregar_planilha_drive(dados["id"], dados["mimeType"])

        if df is not None and not df.empty:
            exibir_interface_pesquisa(df, arquivo_selecionado)
        else:
            st.warning("A planilha selecionada está vazia ou não pôde ser lida.")


def exibir_interface_pesquisa(df: pd.DataFrame, nome_arquivo: str):
    """Exibe os dados com busca dinâmica em tempo real."""
    st.success(f"Planilha **{nome_arquivo}** carregada com sucesso ({len(df)} registros).", icon="📊")
    st.markdown("---")

    termo_busca = st.text_input("🔎 Digite para pesquisar (Nome, CPF, Matrícula, Processo, etc.):", "")

    if termo_busca:
        mascara = df.astype(str).apply(
            lambda col: col.str.contains(termo_busca, case=False, na=False)
        ).any(axis=1)
        df_filtrado = df[mascara]
    else:
        df_filtrado = df

    col_m1, col_m2 = st.columns(2)
    col_m1.metric("Registros Encontrados", len(df_filtrado))

    # Identifica a coluna de dias remidos para calcular o totalizador
    colunas_dias = [c for c in df_filtrado.columns if "dia" in c.lower() or "remi" in c.lower()]
    if colunas_dias:
        col_dias = colunas_dias[0]
        total_dias = pd.to_numeric(df_filtrado[col_dias], errors='coerce').sum()
        col_m2.metric(f"Total de {col_dias}", f"{int(total_dias) if pd.notnull(total_dias) else 0} dias")

    st.dataframe(
        df_filtrado,
        use_container_width=True,
        hide_index=True
    )
