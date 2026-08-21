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


@st.cache_data(ttl=300, show_spinner=False)
def mapear_estrutura_pastas(folder_id):
    """Varre o Drive e retorna um dicionário com todos os caminhos de pastas e seus respectivos IDs."""
    service = conectar_google_drive()
    if not service:
        return {}

    mapa_pastas = {"📂 [Pasta Principal]": folder_id}

    def buscar_subpastas(parent_id, caminho_pai):
        mime_folder = "application/vnd.google-apps.folder"
        try:
            query = f"'{parent_id}' in parents and mimeType = '{mime_folder}' and trashed = false"
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=100
            ).execute()

            for subpasta in results.get("files", []):
                caminho_completo = f"{caminho_pai} / {subpasta['name']}"
                mapa_pastas[f"📁 {caminho_completo}"] = subpasta["id"]
                # Busca recursiva para sub-subpastas
                buscar_subpastas(subpasta["id"], caminho_completo)
        except Exception as e:
            st.warning(f"Erro ao mapear a pasta {caminho_pai}: {e}")

    buscar_subpastas(folder_id, "Principal")
    return mapa_pastas


def listar_arquivos_da_pasta(folder_id):
    """Lista apenas as planilhas localizadas diretamente dentro da pasta selecionada."""
    service = conectar_google_drive()
    if not service:
        return []

    extensoes_validas = ('.xlsx', '.xls', '.ods', '.csv')
    mime_google_sheets = "application/vnd.google-apps.spreadsheet"

    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=100
        ).execute()

        itens = results.get("files", [])
        
        arquivos = []
        for item in itens:
            nome_lc = item["name"].lower()
            if nome_lc.endswith(extensoes_validas) or item["mimeType"] == mime_google_sheets:
                arquivos.append(item)

        return arquivos
    except Exception as e:
        st.error(f"Erro ao buscar arquivos na pasta selecionada: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def carregar_planilha_drive(file_id, mime_type, nome_arquivo):
    """Baixa e interpreta a planilha escolhida."""
    service = conectar_google_drive()
    if not service:
        return None

    try:
        nome_lc = nome_arquivo.lower()

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

        if nome_lc.endswith('.csv'):
            return pd.read_csv(fh)
        elif nome_lc.endswith('.ods'):
            return pd.read_excel(fh, engine='odf')
        else:
            return pd.read_excel(fh)

    except Exception as e:
        st.error(f"Erro ao carregar a planilha **{nome_arquivo}**: {e}")
        return None


def renderizar():
    st.subheader("🔍 Pesquisa e Consulta de Remição de Pena")
    st.markdown("Navegue pelas pastas do **Google Drive** e selecione a planilha desejada.")

    if "gcp_service_account" not in st.secrets:
        st.error("❌ Credenciais do Google Drive não configuradas no `st.secrets`.")
        return

    root_folder_id = st.secrets["gcp_service_account"].get("pasta_id")
    if not root_folder_id:
        st.error("❌ Parâmetro `pasta_id` ausente no `st.secrets`.")
        return

    # 1º PASSO: Mapear e selecionar a Pasta / Subpasta
    with st.spinner("Mapeando pastas e subpastas no Google Drive..."):
        mapa_pastas = mapear_estrutura_pastas(root_folder_id)

    if not mapa_pastas:
        st.warning("Nenhuma pasta foi encontrada ou permissão negada.")
        return

    col_pasta, col_btn = st.columns([3, 1])
    with col_pasta:
        pasta_selecionada_nome = st.selectbox(
            "📂 1. Escolha a Pasta / Subpasta:",
            options=list(mapa_pastas.keys())
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Pastas", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    pasta_id_atual = mapa_pastas[pasta_selecionada_nome]

    # 2º PASSO: Listar os arquivos contidos na pasta escolhida
    arquivos = listar_arquivos_da_pasta(pasta_id_atual)

    if not arquivos:
        st.info("ℹ️ Não há arquivos de planilha nesta pasta específica.")
        return

    opcoes_arquivos = {arq["name"]: arq for arq in arquivos}

    arquivo_selecionado_nome = st.selectbox(
        "📄 2. Escolha o Arquivo / Planilha:",
        options=list(opcoes_arquivos.keys())
    )

    # 3º PASSO: Carregar e exibir a planilha escolhida
    if arquivo_selecionado_nome:
        dados_arquivo = opcoes_arquivos[arquivo_selecionado_nome]
        with st.spinner(f"Lendo **{arquivo_selecionado_nome}**..."):
            df = carregar_planilha_drive(dados_arquivo["id"], dados_arquivo["mimeType"], arquivo_selecionado_nome)

        if df is not None and not df.empty:
            exibir_interface_pesquisa(df, arquivo_selecionado_nome)
        else:
            st.warning("A planilha selecionada está vazia ou não pôde ser processada.")


def exibir_interface_pesquisa(df: pd.DataFrame, nome_arquivo: str):
    """Exibe o mecanismo de busca e métricas na planilha aberta."""
    st.success(f"Planilha **{nome_arquivo}** aberta ({len(df)} registros).", icon="📊")
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
