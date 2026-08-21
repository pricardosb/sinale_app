import io
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# Importações para integração com o Google Drive
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


# =============================================================================
# WRAPPER AUXILIAR PARA COMPATIBILIDADE DE ARQUIVOS
# =============================================================================

class DriveFileWrapper:
    """Simula o comportamento do UploadedFile do Streamlit para arquivos do Drive."""
    def __init__(self, name: str, content_bytes: bytes):
        self.name = name
        self._bytes = content_bytes

    def getvalue(self) -> bytes:
        return self._bytes


# =============================================================================
# INTEGRACAO E CONEXAO COM GOOGLE DRIVE
# =============================================================================

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
def obter_todas_pastas(root_folder_id: str):
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


def listar_arquivos_das_pastas(folder_ids: list):
    """Lista as planilhas contidas em todas as pastas/subpastas selecionadas."""
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
def baixar_arquivo_drive_em_memoria(file_id: str, mime_type: str, nome_arquivo: str):
    """Baixa o arquivo do Google Drive diretamente em memória (BytesIO)."""
    service = conectar_google_drive()
    if not service:
        return None

    try:
        if mime_type == "application/vnd.google-apps.spreadsheet":
            request = service.files().export_media(
                fileId=file_id,
                mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            if not nome_arquivo.lower().endswith('.xlsx'):
                nome_arquivo += ".xlsx"
        else:
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()

        fh.seek(0)
        return DriveFileWrapper(nome_arquivo, fh.getvalue())

    except Exception as e:
        st.error(f"Erro ao baixar o arquivo **{nome_arquivo}**: {e}")
        return None


# =============================================================================
# FUNÇÕES AUXILIARES DE SUPORTE
# =============================================================================

def titulo_estilizado(texto: str):
    st.markdown(
        f"""
        <div style="background-color: #1E3A8A; padding: 12px; border-radius: 8px; margin-bottom: 20px;">
            <h2 style="color: white; text-align: center; margin: 0; font-family: sans-serif;">{texto}</h2>
        </div>
        """,
        unsafe_allow_html=True
    )

def extrair_mes_ano_do_nome(nome_arquivo: str) -> str:
    padrao = r'(0[1-9]|1[0-2])[\/\_\-]?([2-9]\d{3})'
    m = re.search(padrao, nome_arquivo)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return "SEM MÊS/ANO"

def deduplicar_colunas(colunas) -> list:
    vistos = {}
    novas = []
    for c in colunas:
        nome = str(c).strip()
        if nome in vistos:
            vistos[nome] += 1
            novas.append(f"{nome}_{vistos[nome]}")
        else:
            vistos[nome] = 0
            novas.append(nome)
    return novas

def obter_nome_coluna_por_letra(df, colunas_originais, letra):
    if not letra:
        return None
    letra = letra.upper()
    idx = 0
    for char in letra:
        idx = idx * 26 + (ord(char) - ord('A') + 1)
    idx -= 1
    if 0 <= idx < len(colunas_originais):
        return colunas_originais[idx]
    return None

def formatar_datas_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df_copy = df.copy()
    for col in df_copy.columns:
        if any(term in str(col).lower() for term in ["data", "entrada", "saida"]):
            try:
                df_copy[col] = pd.to_datetime(df_copy[col], errors='ignore')
            except:
                pass
    return df_copy

def gerar_config_largura_colunas(df: pd.DataFrame, colunas: list) -> dict:
    config = {}
    for col in colunas:
        config[col] = st.column_config.TextColumn(col)
    return config


# =============================================================================
# MÓDULO PRINCIPAL - PESQUISA PARA REMIÇÃO
# =============================================================================

def render_pesquisa_remicao():
    titulo_estilizado("Pesquisa e Consulta de Remição de Pena")

    if "uploader_key" not in st.session_state:
        st.session_state["uploader_key"] = 0

    # -------------------------------------------------------------------------
    # PASSO 1: NAVEGAÇÃO E SELEÇÃO NO GOOGLE DRIVE
    # -------------------------------------------------------------------------
    st.subheader("1. Seleção de Pastas e Planilhas no Google Drive")

    if "gcp_service_account" not in st.secrets:
        st.error("❌ Credenciais do Google Drive não configuradas no `st.secrets`.")
        return

    root_folder_id = st.secrets["gcp_service_account"].get("pasta_id")
    if not root_folder_id:
        st.error("❌ Parâmetro `pasta_id` ausente no `st.secrets`.")
        return

    # Mapeamento dinâmico de pastas e subpastas
    with st.spinner("Mapeando pastas e subpastas do Google Drive..."):
        lista_pastas = obter_todas_pastas(root_folder_id)

    if not lista_pastas:
        st.warning("Nenhuma pasta ou subpasta foi encontrada no Google Drive.")
        return

    mapa_pastas = {}
    for p in lista_pastas:
        nome_orig = p["name"]
        chave = nome_orig if nome_orig not in mapa_pastas else f"{nome_orig} ({p['id'][:4]})"
        mapa_pastas[chave] = p["id"]

    col_p1, col_p2 = st.columns([3, 1])
    with col_p1:
        pastas_selecionadas_nomes = st.multiselect(
            "📁 Selecione a(s) Pasta(s) / Subpasta(s) para pesquisar:",
            options=list(mapa_pastas.keys()),
            default=list(mapa_pastas.keys())[0] if mapa_pastas else [],
            key=f"select_drive_pastas_{st.session_state['uploader_key']}"
        )
    with col_p2:
        if st.button("🔄 Recarregar Pastas", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    if not pastas_selecionadas_nomes:
        st.info("Selecione ao menos uma pasta para listar as planilhas.")
        return

    folder_ids_selecionados = [mapa_pastas[nome] for nome in pastas_selecionadas_nomes]

    # Lista arquivos das pastas selecionadas
    arquivos_drive = listar_arquivos_das_pastas(folder_ids_selecionados)

    if not arquivos_drive:
        st.warning("Nenhum arquivo de planilha encontrado nas pastas selecionadas.")
        return

    mapa_arquivos = {}
    for arq in arquivos_drive:
        nome_arq = arq["name"]
        chave_arq = nome_arq if nome_arq not in mapa_arquivos else f"{nome_arq} ({arq['id'][:4]})"
        mapa_arquivos[chave_arq] = arq

    arquivos_selecionados_nomes = st.multiselect(
        "📄 Selecione a(s) Planilha(s) que deseja processar:",
        options=list(mapa_arquivos.keys()),
        default=list(mapa_arquivos.keys()),
        key=f"select_drive_files_{st.session_state['uploader_key']}"
    )

    if not arquivos_selecionados_nomes:
        st.info("Selecione ao menos uma planilha para continuar.")
        return

    st.info(f"📊 **Quantidade de planilhas selecionadas:** {len(arquivos_selecionados_nomes)}")

    # -------------------------------------------------------------------------
    # PASSO 2: DOWNLOAD EM MEMÓRIA E CONFIGURAÇÃO DE ABAS/CAMPOS
    # -------------------------------------------------------------------------
    fazer_upload_btn = st.button("Configurar Abas e Campos das Planilhas Selecionadas", key="btn_fazer_upload_op3", type="primary")

    if fazer_upload_btn:
        st.session_state["executar_config"] = True
        st.session_state["rolar_apos_upload"] = True
        st.success("Planilhas carregadas com sucesso! Configure as abas e colunas abaixo:")

    if st.session_state.get("executar_config"):
        # Realiza o download dos arquivos selecionados do Drive para objetos em memória
        uploaded_files = []
        with st.spinner("Baixando planilhas selecionadas do Google Drive..."):
            for nome_chave in arquivos_selecionados_nomes:
                dados_arq = mapa_arquivos[nome_chave]
                file_obj = baixar_arquivo_drive_em_memoria(dados_arq["id"], dados_arq["mimeType"], dados_arq["name"])
                if file_obj:
                    uploaded_files.append(file_obj)

        settings = {}
        for f_idx, f in enumerate(uploaded_files):
            file_key = f"{f_idx}_{f.name}"
            f_bytes = f.getvalue()
            file_ext = f.name.split('.')[-1].lower()
            
            try:
                engine_val = 'odf' if file_ext == 'ods' else None
                xl = pd.ExcelFile(io.BytesIO(f_bytes), engine=engine_val)
                sheets_available = xl.sheet_names
            except Exception as e:
                st.error(f"Erro ao ler o arquivo {f.name}: {e}.")
                continue

            pref_sheets = [s for s in sheets_available if any(p in s.strip().upper() for p in ["COM REMUNER", "SEM REMUNER", "DEM_COM", "DEM_SEM"])]

            if pref_sheets:
                default_sheets = pref_sheets
                is_fallback = False
            else:
                default_sheets = [sheets_available[0]] if sheets_available else []
                is_fallback = True

            with st.expander(f"📁 Configurações para: Arquivo {f_idx+1} - {f.name}", expanded=True):
                selected_sheets = st.multiselect(
                    f"Selecione aba(s) para {f.name}",
                    sheets_available,
                    default=default_sheets,
                    key=f"sheets_{file_key}_{st.session_state['uploader_key']}"
                )

                sheet_config = {}
                for i, sheet in enumerate(selected_sheets):
                    st.markdown(f"**Aba: `{sheet}`**")

                    sheet_upper = sheet.strip().upper()
                    if "DEM_COM" in sheet_upper:
                        default_header = 17
                    elif "DEM_SEM" in sheet_upper:
                        default_header = 19
                    elif any(p in sheet_upper for p in ["COM REMUNER", "SEM REMUNER"]):
                        default_header = 11
                    else:
                        default_header = 10 if is_fallback else 11

                    header_row = st.number_input(
                        f"Linha do cabeçalho para aba '{sheet}'",
                        value=default_header,
                        min_value=1,
                        key=f"head_{file_key}_{sheet}_{st.session_state['uploader_key']}"
                    )

                    try:
                        df_preview = pd.read_excel(io.BytesIO(f_bytes), sheet_name=sheet, header=header_row - 1, nrows=0, engine=engine_val)
                        cols_aba = [str(c).strip() for c in df_preview.columns]
                    except:
                        cols_aba = []

                    default_col = None
                    for c in cols_aba:
                        c_up = str(c).strip().upper()
                        if c_up in ["NOME DO INTERNO", "NOME DO INTERNO "]:
                            default_col = c
                            break
                    if not default_col:
                        for c in cols_aba:
                            if str(c).strip().upper() == "NOME":
                                default_col = c
                                break
                    if not default_col:
                        for c in cols_aba:
                            if str(c).strip().upper().startswith("NOME"):
                                default_col = c
                                break
                    if not default_col:
                        for c in cols_aba:
                            if "NOME" in str(c).strip().upper():
                                default_col = c
                                break
                    if not default_col and len(cols_aba) > 8:
                        default_col = cols_aba[8]
                    elif not default_col and cols_aba:
                        default_col = cols_aba[0]

                    opcoes_colunas = ["--- Não pesquisar nesta aba ---"] + cols_aba
                    default_idx = opcoes_colunas.index(default_col) if default_col in opcoes_colunas else 0

                    col_escolhida = st.selectbox(
                        f"Selecione o campo (coluna) para a pesquisa na aba '{sheet}':",
                        opcoes_colunas,
                        index=default_idx,
                        key=f"col_search_{file_key}_{sheet}_{st.session_state['uploader_key']}"
                    )

                    sheet_config[sheet] = {
                        "header_idx": header_row - 1,
                        "col_busca": col_escolhida if col_escolhida != "--- Não pesquisar nesta aba ---" else None
                    }
                    st.markdown("---")

                settings[file_key] = sheet_config

        btn_consolidar = st.button("🔍 Carregar e Consolidar Dados para Pesquisa", key="btn_consolidar_op3", type="primary")

        # Rolagem suave automática
        if st.session_state.get("rolar_apos_upload"):
            components.html(
                """
                <script>
                    function rolarAteOFinal() {
                        const doc = window.parent.document;
                        const container = doc.querySelector('section.main') || doc.querySelector('[data-testid="stMain"]') || doc.querySelector('[data-testid="stAppViewContainer"]') || doc.documentElement;
                        if (container) {
                            container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
                        }
                    }
                    setTimeout(rolarAteOFinal, 400);
                    setTimeout(rolarAteOFinal, 800);
                </script>
                """,
                height=0
            )
            st.session_state["rolar_apos_upload"] = False

        # ---------------------------------------------------------------------
        # PASSO 3: CONSOLIDAÇÃO DOS DADOS E APLICAÇÃO DAS REGRAS DE NEGÓCIO
        # ---------------------------------------------------------------------
        if btn_consolidar:
            all_results = []
            for f_idx, f in enumerate(uploaded_files):
                file_key = f"{f_idx}_{f.name}"
                f_bytes = f.getvalue()
                file_ext = f.name.split('.')[-1].lower()
                engine_val = 'odf' if file_ext == 'ods' else None
                
                try:
                    xl = pd.ExcelFile(io.BytesIO(f_bytes), engine=engine_val)
                    mes_ano_arquivo = extrair_mes_ano_do_nome(f.name)
                except:
                    mes_ano_arquivo = "SEM MÊS/ANO"

                file_cfg = settings.get(file_key, {})
                for sheet, cfg in file_cfg.items():
                    try:
                        df_tmp = pd.read_excel(io.BytesIO(f_bytes), sheet_name=sheet, header=cfg["header_idx"], engine=engine_val)
                        df_tmp.columns = [str(c).strip() for c in df_tmp.columns]
                        df_tmp.columns = deduplicar_colunas(df_tmp.columns)

                        col_pedida = cfg.get("col_busca")
                        target_col = None
                        if col_pedida:
                            for c in df_tmp.columns:
                                if str(c).strip().upper() == str(col_pedida).strip().upper():
                                    target_col = c
                                    break
                        if not target_col:
                            for c in df_tmp.columns:
                                if "NOME DO INTERNO" in str(c).strip().upper():
                                    target_col = c
                                    break
                        if not target_col:
                            for c in df_tmp.columns:
                                if "NOME" in str(c).strip().upper():
                                    target_col = c
                                    break
                        if not target_col and len(df_tmp.columns) > 8:
                            target_col = df_tmp.columns[8]
                        elif not target_col and len(df_tmp.columns) > 0:
                            target_col = df_tmp.columns[0]

                        if target_col and target_col in df_tmp.columns:
                            colunas_originais = list(df_tmp.columns)

                            df_tmp["Campo Pesquisado"] = target_col

                            val_nome = df_tmp[target_col].astype(str).str.strip()
                            df_tmp["Nome (Visualização)"] = val_nome
                            df_tmp["NOME_LIMPO"] = val_nome.str.upper()

                            df_tmp = df_tmp[~df_tmp["NOME_LIMPO"].isin(['', 'NAN', 'NONE', '0', 'NAT', 'NC', 'N/C'])].copy()

                            aba_upper = sheet.strip().upper()
                            is_dem_com = "DEM_COM" in aba_upper
                            is_dem_sem = "DEM_SEM" in aba_upper
                            is_com_remuner = "COM REMUNER" in aba_upper
                            is_sem_remuner = "SEM REMUNER" in aba_upper
                            col_f = obter_nome_coluna_por_letra(df_tmp, colunas_originais, 'F')
                            
                            usar_padrao_antigo = False
                            usar_dem_sem_antigo = False

                            is_03_a_05_2023 = False
                            is_06_a_07_2023 = False
                            is_08_2023 = False

                            if mes_ano_arquivo != "SEM MÊS/ANO":
                                try:
                                    mes_str, ano_str = mes_ano_arquivo.split('/')
                                    mes_val, ano_val = int(mes_str), int(ano_str)
                                    
                                    if ano_val == 2023 and mes_val in [3, 4, 5]:
                                        is_03_a_05_2023 = True
                                    elif ano_val == 2023 and mes_val in [6, 7]:
                                        is_06_a_07_2023 = True
                                    elif ano_val == 2023 and mes_val == 8:
                                        is_08_2023 = True

                                    if ano_val < 2025 or (ano_val == 2025 and mes_val < 9):
                                        usar_padrao_antigo = True

                                    if ano_val < 2019 or (ano_val == 2019 and mes_val < 11):
                                        usar_dem_sem_antigo = True
                                except Exception:
                                    pass

                            def extrair_dados_e_categoria(row):
                                if is_03_a_05_2023:
                                    if is_dem_com or is_com_remuner:
                                        cat = "COM REMUNERAÇÃO"
                                        letras = ["I", "B", "T", "V", "W", "X", "Y"]
                                    elif is_dem_sem or is_sem_remuner:
                                        cat = "SEM REMUNERAÇÃO"
                                        letras = ["J", "B", "S", "U", "V", "W", "X"]
                                    else:
                                        val_f = row[col_f] if (col_f and col_f in row) else None
                                        is_sim = str(val_f).strip().upper() == "SIM" if pd.notna(val_f) else False
                                        cat = "COM REMUNERAÇÃO" if is_sim else "SEM REMUNERAÇÃO"
                                        letras = ["I", "B", "T", "V", "W", "X", "Y"] if is_sim else ["J", "B", "S", "U", "V", "W", "X"]
                                        
                                elif is_06_a_07_2023:
                                    if is_dem_com or is_com_remuner:
                                        cat = "COM REMUNERAÇÃO"
                                        letras = ["I", "B", "U", "W", "X", "Y", "Z"]
                                    elif is_dem_sem or is_sem_remuner:
                                        cat = "SEM REMUNERAÇÃO"
                                        letras = ["J", "B", "S", "V", "W", "X", "Y"]
                                    else:
                                        val_f = row[col_f] if (col_f and col_f in row) else None
                                        is_sim = str(val_f).strip().upper() == "SIM" if pd.notna(val_f) else False
                                        cat = "COM REMUNERAÇÃO" if is_sim else "SEM REMUNERAÇÃO"
                                        letras = ["I", "B", "U", "W", "X", "Y", "Z"] if is_sim else ["J", "B", "S", "V", "W", "X", "Y"]

                                elif is_08_2023:
                                    if is_dem_com or is_com_remuner:
                                        cat = "COM REMUNERAÇÃO"
                                        letras = ["I", "B", "R", "T", "U", "V", "W"]
                                    elif is_dem_sem or is_sem_remuner:
                                        cat = "SEM REMUNERAÇÃO"
                                        letras = ["I", "B", "Q", "S", "T", "U", "V"]
                                    else:
                                        val_f = row[col_f] if (col_f and col_f in row) else None
                                        is_sim = str(val_f).strip().upper() == "SIM" if pd.notna(val_f) else False
                                        cat = "COM REMUNERAÇÃO" if is_sim else "SEM REMUNERAÇÃO"
                                        letras = ["I", "B", "R", "T", "U", "V", "W"] if is_sim else ["I", "B", "Q", "S", "T", "U", "V"]

                                else:
                                    if is_dem_com:
                                        cat = "COM REMUNERAÇÃO"
                                        letras = ["I", "B", None, "S", "T", "U", "V"]

                                    elif is_dem_sem:
                                        cat = "SEM REMUNERAÇÃO"
                                        if usar_dem_sem_antigo:
                                            letras = ["I", "B", "Y", "R", "S", "T", "U"]
                                        else:
                                            letras = ["I", "B", "Y", "S", "T", "U", "V"]

                                    elif is_com_remuner:
                                        cat = "COM REMUNERAÇÃO"
                                        if usar_padrao_antigo:
                                            letras = ["I", "B", "Q", "S", "T", "U", "V"]
                                        else:
                                            letras = ["B", "I", "J", "T", "U", "V", "W"]

                                    elif is_sem_remuner:
                                        cat = "SEM REMUNERAÇÃO"
                                        letras = ["I", "B", "W", "R", "S", "T", "U"]

                                    else:
                                        val_f = row[col_f] if (col_f and col_f in row) else None
                                        is_sim = str(val_f).strip().upper() == "SIM" if pd.notna(val_f) else False

                                        cat = "COM REMUNERAÇÃO" if is_sim else "SEM REMUNERAÇÃO"
                                        letras = ["J", "C", "X", "S", "T", "U", "V"]

                                row_vals = {
                                    "Categoria_Aba": cat,
                                    "LABEL_EXIBICAO": f"{mes_ano_arquivo} - {sheet}"
                                }
                                for idx_p, let in enumerate(letras):
                                    if let is None:
                                        val = ""
                                        header_title = ""
                                    else:
                                        col_n = obter_nome_coluna_por_letra(df_tmp, colunas_originais, let)
                                        val = row[col_n] if col_n and col_n in row else None
                                        header_title = str(col_n) if col_n else f"Campo {idx_p+1}"
                                    row_vals[f"POS_{idx_p}"] = val
                                    row_vals[f"HEADER_{idx_p}"] = header_title

                                return pd.Series(row_vals)

                            res_df = df_tmp.apply(extrair_dados_e_categoria, axis=1)
                            df_tmp["MÊS/ANO"] = res_df["LABEL_EXIBICAO"]

                            df_processed = pd.concat([
                                df_tmp[[
                                    "MÊS/ANO",
                                    "Campo Pesquisado",
                                    "Nome (Visualização)",
                                    "NOME_LIMPO"
                                ]],
                                res_df
                            ], axis=1)
                            all_results.append(df_processed)
                    except Exception as e:
                        st.error(f"Erro ao ler {f.name} - Aba {sheet}: {e}")

            if all_results:
                st.session_state["pesquisa_df"] = pd.concat(all_results, ignore_index=True)
                st.success(f"Dados consolidados com sucesso! **{len(st.session_state['pesquisa_df'])}** registros carregados.")
            else:
                st.warning("Nenhum dado encontrado com as configurações informadas.")
                st.session_state["pesquisa_df"] = None

    # -------------------------------------------------------------------------
    # PASSO 4: EXIBIÇÃO, FILTROS E VISUALIZAÇÃO DOS RESULTADOS
    # -------------------------------------------------------------------------
    if st.session_state.get("pesquisa_df") is not None:
        df_pesq = st.session_state["pesquisa_df"]
        st.markdown("---")
        st.subheader("🔍 Filtros de Visualização e Busca")

        col_ord1, col_ord2 = st.columns([2, 2])
        with col_ord1:
            ordem_escolhida = st.radio(
                "📅 Ordenação por Mês/Ano:",
                ["Crescente (Antigo ➔ Recente)", "Decrescente (Recente ➔ Antigo)"],
                horizontal=True,
                key=f"ordem_radio_{st.session_state['uploader_key']}"
            )
        
        is_ascending = True if "Crescente" in ordem_escolhida else False

        nomes_disponiveis = sorted(df_pesq["Nome (Visualização)"].dropna().unique())
        nomes_selecionados = st.multiselect(
            "🔍 Digite para pesquisar e selecione o(s) nome(s):",
            options=nomes_disponiveis,
            key=f"busca_nomes_{st.session_state['uploader_key']}"
        )

        df_view = df_pesq.copy()
        if nomes_selecionados:
            df_view = df_view[df_view["Nome (Visualização)"].isin(nomes_selecionados)]

        st.metric("Total de Registros Encontrados", len(df_view))

        if not df_view.empty:
            def extrair_chave_data(val):
                try:
                    data_str = str(val).split(' - ')[0].strip()
                    if data_str == "SEM MÊS/ANO":
                        return 999999 if is_ascending else -1
                    m, y = data_str.split('/')
                    return int(y) * 100 + int(m)
                except:
                    return 999999 if is_ascending else -1
            
            df_view['chave_ordenacao'] = df_view['MÊS/ANO'].apply(extrair_chave_data)
            df_view = df_view.sort_values(by=['chave_ordenacao'], ascending=is_ascending).drop(columns=['chave_ordenacao'])

            df_display_all = formatar_datas_dataframe(df_view)

            def formatar_sem_decimal(val):
                if pd.isna(val) or str(val).strip() in ["", "nan", "None"]:
                    return ""
                try:
                    num = float(val)
                    return str(int(round(num)))
                except (ValueError, TypeError):
                    return str(val).strip()

            def conv_num(val):
                try:
                    v_str = str(val).replace(',', '.').strip()
                    return float(v_str) if v_str not in ["", "nan", "None"] else 0.0
                except:
                    return 0.0

            grupos_categorias = [
                ("🟢 COM REMUNERAÇÃO", "COM REMUNERAÇÃO", "com_rem"),
                ("🟡 SEM REMUNERAÇÃO", "SEM REMUNERAÇÃO", "sem_rem")
            ]

            for titulo_grupo, cat_key, prefixo_key in grupos_categorias:
                df_grupo = df_display_all[df_display_all["Categoria_Aba"] == cat_key]

                if not df_grupo.empty:
                    pos_cols = [c for c in df_grupo.columns if str(c).startswith("POS_")]
                    pos_cols.sort(key=lambda x: int(x.split("_")[1]))

                    cabecalhos_padrao = ["NOME", "ORGANIZ", "FUNÇÃO", "ENTRADA", "SAIDA", "PREV", "REAL"]
                    rename_map = {}
                    
                    for idx_p, pos_col in enumerate(pos_cols):
                        if idx_p < len(cabecalhos_padrao):
                            rename_map[pos_col] = cabecalhos_padrao[idx_p]
                        else:
                            rename_map[pos_col] = f"Campo {idx_p+1}"

                    cols_exibir = ["MÊS/ANO"] + pos_cols
                    df_render = df_grupo[cols_exibir].rename(columns=rename_map)

                    if "REAL" in df_render.columns:
                        df_render["REAL"] = df_render["REAL"].apply(formatar_sem_decimal)

                    st.markdown(f"### {titulo_grupo} ({len(df_render)} registro(s))")

                    key_select = f"select_all_{prefixo_key}"
                    if key_select not in st.session_state:
                        st.session_state[key_select] = False

                    col_b1, col_b2, _ = st.columns([1, 1, 4])
                    with col_b1:
                        if st.button("✅ Marcar Todos", key=f"btn_marcar_{prefixo_key}_{st.session_state['uploader_key']}"):
                            st.session_state[key_select] = True
                            st.rerun()
                    with col_b2:
                        if st.button("❌ Desmarcar Todos", key=f"btn_desmarcar_{prefixo_key}_{st.session_state['uploader_key']}"):
                            st.session_state[key_select] = False
                            st.rerun()

                    df_render.insert(0, "SELECIONAR?", st.session_state[key_select])

                    col_config_conteudo = gerar_config_largura_colunas(df_render, df_render.columns.tolist())
                    col_config_conteudo["SELECIONAR?"] = st.column_config.CheckboxColumn("SELECIONAR?", default=False)

                    df_editado_res = st.data_editor(
                        df_render,
                        column_config=col_config_conteudo,
                        use_container_width=True,
                        hide_index=True,
                        key=f"editor_res_{prefixo_key}_{st.session_state['uploader_key']}"
                    )

                    selecionados_grupo = df_editado_res[df_editado_res["SELECIONAR?"] == True]
                    
                    if not selecionados_grupo.empty:
                        st.markdown("---")
                        st.markdown(f"### 📋 Espaço de Visualização dos Registros Selecionados — {titulo_grupo}")
                        
                        grupos_nome = selecionados_grupo.groupby("NOME", sort=False)

                        for nome_interno, df_nome_sel in grupos_nome:
                            organiz_val = ", ".join([str(v) for v in df_nome_sel["ORGANIZ"].dropna().unique() if str(v).strip() != ""])
                            funcao_val = ", ".join([str(v) for v in df_nome_sel["FUNÇÃO"].dropna().unique() if str(v).strip() != ""])
                            saida_val = ", ".join([str(v) for v in df_nome_sel["SAIDA"].dropna().unique() if str(v).strip() != ""])

                            with st.container():
                                st.markdown(
                                    f"""
                                    <div style="background-color: #f8fafc; border-left: 5px solid #1E3A8A; padding: 12px; margin-bottom: 15px; border-radius: 4px;">
                                        <h4 style="margin: 0; color: #1E3A8A;">👤 Interno: {nome_interno}</h4>
                                        <p style="margin: 4px 0 0 0; color: #475569; font-size: 0.9em;">
                                            <b>Organização:</b> {organiz_val if organiz_val else 'N/A'} | 
                                            <b>Função:</b> {funcao_val if funcao_val else 'N/A'} | 
                                            <b>Saída:</b> {saida_val if saida_val else 'N/A'}
                                        </p>
                                    </div>
                                    """,
                                    unsafe_allow_html=True
                                )

                                cols_detalhe = [c for c in df_nome_sel.columns if c != "SELECIONAR?"]
                                st.dataframe(df_nome_sel[cols_detalhe], use_container_width=True, hide_index=True)

                                if "REAL" in df_nome_sel.columns:
                                    soma_horas = sum(conv_num(v) for v in df_nome_sel["REAL"])
                                    st.caption(f"⏱️ **Soma total de Horas Realizadas no período selecionado:** {int(round(soma_horas))} h")


# Alias para garantir compatibilidade com chamadas no app.py (pesquisa.renderizar())
renderizar = render_pesquisa_remicao

# Execução direta se o arquivo for rodado individualmente
if __name__ == "__main__":
    st.set_page_config(page_title="Pesquisa para Remição", layout="wide")
    render_pesquisa_remicao()
