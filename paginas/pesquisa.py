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
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=scopes)
        return build("drive", "v3", credentials=creds)
    except Exception as e:
        st.error(f"Erro na autenticação com o Google Drive: {e}")
        return None


def listar_arquivos_drive(folder_id):
    """Lista arquivos de planilha (.xlsx, .xls, .ods, .csv, Google Sheets) na pasta do Drive."""
    service = conectar_google_drive()
    if not service:
        return []

    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=100
        ).execute()

        itens = results.get("files", [])
        
        extensoes_validas = ('.xlsx', '.xls', '.ods', '.csv')
        mime_google_sheets = "application/vnd.google-apps.spreadsheet"

        arquivos_planilha = []
        for item in itens:
            nome_lc = item["name"].lower()
            if nome_lc.endswith(extensoes_validas) or item["mimeType"] == mime_google_sheets:
                arquivos_planilha.append(item)

        return arquivos_planilha
    except Exception as e:
        st.error(f"Erro ao listar arquivos do Google Drive: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def carregar_planilha_drive(file_id, mime_type, nome_arquivo):
    """Baixa e interpreta planilhas nos formatos .xlsx, .xls, .ods, .csv e Google Sheets."""
    service = conectar_google_drive()
    if not service:
        return None

    try:
        nome_lc = nome_arquivo.lower()

        # Google Sheets nativo -> Exporta como XLSX
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

        # Leitura conforme a extensão
        if nome_lc.endswith('.csv'):
            return pd.read_csv(fh)
        elif nome_lc.endswith('.ods'):
            return pd.read_excel(fh, engine='odf')
        else:
            return pd.read_excel(fh)

    except Exception as e:
        st.error(f"Erro ao processar o arquivo **{nome_arquivo}**: {e}")
        return None


def renderizar():
    st.subheader("🔍 Pesquisa e Consulta de Remição de Pena")
    st.markdown("Consulte relatórios e históricos armazenados na pasta do **Google Drive**.")

    # 1. Verifica credenciais
    if "gcp_service_account" not in st.secrets:
        st.error("❌ As credenciais do Google Drive não foram encontradas no `st.secrets`.")
        return

    # 2. Obtém o ID da pasta
    folder_id = st.secrets["gcp_service_account"].get("pasta_id")
    if not folder_id:
        st.error("❌ O parâmetro `pasta_id` não foi configurado em `[gcp_service_account]` no Secrets.")
        return

    # 3. Busca arquivos na nuvem
    with st.spinner("Conectando ao Google Drive e buscando arquivos..."):
        arquivos = listar_arquivos_drive(folder_id)

    if not arquivos:
        st.warning("⚠️ Nenhum arquivo foi encontrado na pasta configurada.")
        st.info(
            "**Checklist de Verificação:**\n"
            "1. Verifique se a pasta no Google Drive foi compartilhada com o e-mail:\n"
            "   `fluxo-dados-web-cosis@cpfs-web.iam.gserviceaccount.com` (como Leitor ou Editor).\n"
            "2. Confirme se o `pasta_id` no `secrets.toml` está correto.\n"
            "3. Certifique-se de que existem arquivos `.xlsx`, `.xls`, `.ods` ou `.csv` dentro dessa pasta."
        )
        if st.button("🔄 Recarregar Pasta"):
            st.rerun()
        return

    # 4. Seleção da planilha
    opcoes = {arq["name"]: arq for arq in arquivos}

    col_sel, col_ref = st.columns([3, 1])
    with col_sel:
        arquivo_selecionado = st.selectbox(
            "📁 Selecione a planilha que deseja trabalhar/consultar:",
            options=list(opcoes.keys())
        )
    with col_ref:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 5. Carregamento e exibição
    if arquivo_selecionado:
        dados = opcoes[arquivo_selecionado]
        with st.spinner(f"Lendo **{arquivo_selecionado}** do Google Drive..."):
            df = carregar_planilha_drive(dados["id"], dados["mimeType"], arquivo_selecionado)

        if df is not None and not df.empty:
            exibir_interface_pesquisa(df, arquivo_selecionado)
        else:
            st.warning("A planilha selecionada está vazia ou não pôde ser lida.")


def exibir_interface_pesquisa(df: pd.DataFrame, nome_arquivo: str):
    """Exibe a interface interativa de busca nos dados da planilha selecionada."""
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

    # Tenta somar colunas relativas a dias remidos
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
