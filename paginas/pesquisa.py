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


def listar_arquivos_recursivo(service, folder_id, caminho_atual=""):
    """Percorre recursivamente a pasta e todas as subpastas encontrando planilhas."""
    extensoes_validas = ('.xlsx', '.xls', '.ods', '.csv')
    mime_google_sheets = "application/vnd.google-apps.spreadsheet"
    mime_folder = "application/vnd.google-apps.folder"

    arquivos_encontrados = []

    try:
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType)",
            pageSize=1000
        ).execute()

        itens = results.get("files", [])

        for item in itens:
            mime = item["mimeType"]
            nome = item["name"]

            if mime == mime_folder:
                # É uma subpasta -> Entra e busca recursivamente
                novo_caminho = f"{caminho_atual}{nome} / "
                sub_itens = listar_arquivos_recursivo(service, item["id"], novo_caminho)
                arquivos_encontrados.extend(sub_itens)
            else:
                # É um arquivo -> Verifica se é planilha
                nome_lc = nome.lower()
                if nome_lc.endswith(extensoes_validas) or mime == mime_google_sheets:
                    nome_exibicao = f"📁 {caminho_atual}{nome}" if caminho_atual else f"📄 {nome}"
                    item_copia = item.copy()
                    item_copia["nome_exibicao"] = nome_exibicao
                    arquivos_encontrados.append(item_copia)

    except Exception as e:
        st.warning(f"Aviso ao varrer subpasta ({caminho_atual}): {e}")

    return arquivos_encontrados


def listar_arquivos_drive(folder_id):
    """Função principal que inicia a varredura na pasta raiz configurada."""
    service = conectar_google_drive()
    if not service:
        return []
    return listar_arquivos_recursivo(service, folder_id)


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
    st.markdown("Consulte relatórios e históricos armazenados na pasta e subpastas do **Google Drive**.")

    # 1. Verifica credenciais
    if "gcp_service_account" not in st.secrets:
        st.error("❌ As credenciais do Google Drive não foram encontradas no `st.secrets`.")
        return

    # 2. Obtém o ID da pasta principal
    folder_id = st.secrets["gcp_service_account"].get("pasta_id")
    if not folder_id:
        st.error("❌ O parâmetro `pasta_id` não foi configurado em `[gcp_service_account]` no Secrets.")
        return

    # 3. Busca arquivos em todas as pastas e subpastas
    with st.spinner("Varrendo pasta principal e subpastas no Google Drive..."):
        arquivos = listar_arquivos_drive(folder_id)

    if not arquivos:
        st.warning("⚠️ Nenhuma planilha foi encontrada na pasta principal ou nas subpastas.")
        st.info(
            "**Checklist de Verificação:**\n"
            "1. Certifique-se de que a pasta principal foi compartilhada com o e-mail:\n"
            "   `fluxo-dados-web-cosis@cpfs-web.iam.gserviceaccount.com` (como Editor).\n"
            "2. Verifique se existem arquivos com extensão `.xlsx`, `.xls`, `.ods`, `.csv` ou Planilhas do Google."
        )
        if st.button("🔄 Recarregar Pasta"):
            st.rerun()
        return

    # 4. Ordena e mapeia para a seleção
    arquivos_ordenados = sorted(arquivos, key=lambda x: x["nome_exibicao"])
    opcoes = {arq["nome_exibicao"]: arq for arq in arquivos_ordenados}

    col_sel, col_ref = st.columns([3, 1])
    with col_sel:
        selecao_formatada = st.selectbox(
            "📁 Selecione a planilha (organizadas por subpasta):",
            options=list(opcoes.keys())
        )
    with col_ref:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Atualizar Lista", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    # 5. Carregamento e exibição
    if selecao_formatada:
        dados = opcoes[selecao_formatada]
        with st.spinner(f"Lendo **{dados['name']}** do Google Drive..."):
            df = carregar_planilha_drive(dados["id"], dados["mimeType"], dados["name"])

        if df is not None and not df.empty:
            exibir_interface_pesquisa(df, dados["name"])
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

    # Identifica colunas de dias remidos para totalização
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
