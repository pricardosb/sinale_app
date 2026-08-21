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
def obter_todas_pastas(root_folder_id):
    """Mapeia todas as pastas e subpastas utilizando seus nomes originais."""
    service = conectar_google_drive()
    if not service:
        return []

    pastas = []
    
    # Obtém nome original da pasta raiz
    try:
        raiz_info = service.files().get(fileId=root_folder_id, fields="id, name").execute()
        pastas.append({"id": raiz_info["id"], "name": raiz_info["name"]})
    except Exception:
        pastas.append({"id": root_folder_id, "name": "Pasta Principal"})

    def buscar_subpastas(parent_id):
        mime_folder = "application/vnd.google-apps.folder"
        try:
            query = f"'{parent_id}' in parents and mimeType = '{mime_folder}' and trashed = false"
            results = service.files().list(
                q=query,
                fields="files(id, name)",
                pageSize=100
            ).execute()

            for subpasta in results.get("files", []):
                pastas.append({"id": subpasta["id"], "name": subpasta["name"]})
                buscar_subpastas(subpasta["id"])
        except Exception as e:
            st.warning(f"Erro ao buscar subpastas de {parent_id}: {e}")

    buscar_subpastas(root_folder_id)
    return pastas


def listar_arquivos_das_pastas(folder_ids):
    """Lista as planilhas contidas em todas as pastas selecionadas."""
    service = conectar_google_drive()
    if not service or not folder_ids:
        return []

    extensoes_validas = ('.xlsx', '.xls', '.ods', '.csv')
    mime_google_sheets = "application/vnd.google-apps.spreadsheet"

    arquivos = []
    for f_id in folder_ids:
        try:
            query = f"'{f_id}' in parents and trashed = false"
            results = service.files().list(
                q=query,
                fields="files(id, name, mimeType)",
                pageSize=100
            ).execute()

            for item in results.get("files", []):
                nome_lc = item["name"].lower()
                if nome_lc.endswith(extensoes_validas) or item["mimeType"] == mime_google_sheets:
                    arquivos.append(item)
        except Exception as e:
            st.error(f"Erro ao listar arquivos da pasta {f_id}: {e}")

    return arquivos


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
    st.markdown("Selecione uma ou mais pastas e planilhas do **Google Drive** para consultar os dados.")

    if "gcp_service_account" not in st.secrets:
        st.error("❌ Credenciais do Google Drive não configuradas no `st.secrets`.")
        return

    root_folder_id = st.secrets["gcp_service_account"].get("pasta_id")
    if not root_folder_id:
        st.error("❌ Parâmetro `pasta_id` ausente no `st.secrets`.")
        return

    # 1. Carrega todas as pastas mantendo os nomes originais
    with st.spinner("Mapeando estrutura de pastas..."):
        lista_pastas = obter_todas_pastas(root_folder_id)

    if not lista_pastas:
        st.warning("Nenhuma pasta foi encontrada no Google Drive.")
        return

    # Mapeia Nome Original -> ID (trata duplicados se houverem nomes idênticos em locais diferentes)
    mapa_pastas = {}
    for p in lista_pastas:
        nome_orig = p["name"]
        chave = nome_orig if nome_orig not in mapa_pastas else f"{nome_orig} ({p['id'][:4]})"
        mapa_pastas[chave] = p["id"]

    # 1º PASSO: CAIXA DE ROLAGEM MULTI-SELEÇÃO DE PASTAS
    st.markdown("**1. Selecione a(s) Pasta(s):**")
    col_pastas, col_btn = st.columns([3, 1])
    
    with col_pastas:
        with st.container(height=150):
            pastas_selecionadas_nomes = st.multiselect(
                "Marque uma ou mais pastas para buscar arquivos:",
                options=list(mapa_pastas.keys()),
                default=list(mapa_pastas.keys())[0] if mapa_pastas else [],
                label_visibility="collapsed"
            )

    with col_btn:
        if st.button("🔄 Recarregar Lista", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not pastas_selecionadas_nomes:
        st.info("Selecione ao menos uma pasta na caixa acima.")
        return

    folder_ids_selecionados = [mapa_pastas[nome] for nome in pastas_selecionadas_nomes]

    # 2º PASSO: BUSCA ARQUIVOS DAS PASTAS SELECIONADAS
    arquivos = listar_arquivos_das_pastas(folder_ids_selecionados)

    if not arquivos:
        st.info("ℹ️ Nenhum arquivo de planilha foi encontrado nas pastas selecionadas.")
        return

    mapa_arquivos = {}
    for arq in arquivos:
        nome_arq = arq["name"]
        chave_arq = nome_arq if nome_arq not in mapa_arquivos else f"{nome_arq} ({arq['id'][:4]})"
        mapa_arquivos[chave_arq] = arq

    # 2º PASSO: CAIXA DE ROLAGEM MULTI-SELEÇÃO DE PLANILHAS
    st.markdown("**2. Selecione a(s) Planilha(s) para Consulta:**")
    with st.container(height=150):
        arquivos_selecionados_nomes = st.multiselect(
            "Marque uma ou mais planilhas para abrir e combinar os dados:",
            options=list(mapa_arquivos.keys()),
            default=[list(mapa_arquivos.keys())[0]] if mapa_arquivos else [],
            label_visibility="collapsed"
        )

    if not arquivos_selecionados_nomes:
        st.info("Selecione ao menos uma planilha para carregar os dados.")
        return

    # 3º PASSO: LEITURA E CONSOLIDAÇÃO DOS DADOS
    dfs_carregados = []
    with st.spinner("Lendo e unificando planilhas selecionadas..."):
        for nome_chave in arquivos_selecionados_nomes:
            dados_arq = mapa_arquivos[nome_chave]
            df = carregar_planilha_drive(dados_arq["id"], dados_arq["mimeType"], dados_arq["name"])
            if df is not None and not df.empty:
                df["_Arquivo_Origem"] = dados_arq["name"]
                dfs_carregados.append(df)

    if dfs_carregados:
        df_consolidado = pd.concat(dfs_carregados, ignore_index=True)
        exibir_interface_pesquisa(df_consolidado, len(arquivos_selecionados_nomes))
    else:
        st.warning("As planilhas selecionadas estão vazias ou não puderam ser lidas.")


def exibir_interface_pesquisa(df: pd.DataFrame, qtd_arquivos: int):
    """Exibe o mecanismo de busca e métricas agregadas."""
    st.success(f"Carregado(s) **{qtd_arquivos} arquivo(s)** com **{len(df)} registros** no total.", icon="📊")
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
