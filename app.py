import streamlit as st
import pandas as pd
import io
from google.oauth2 import service_account
from googleapiclient.discovery import build

# ID da sua pasta no Google Drive
FOLDER_ID = "1ZeCu40Bzt1hb1BsgNArG_zKR54GPcuOY"

# -----------------------------------------------------------------------------
# 1. LISTAR E FILTRAR ARQUIVOS DA PASTA (Apenas números e ordenados)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def listar_arquivos_drive(folder_id):
    try:
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        service = build('drive', 'v3', credentials=creds)
        
        query = f"'{folder_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        arquivos = results.get('files', [])
        
        # Filtra apenas arquivos cujos nomes comecem com números (0 a 9)
        arquivos_filtrados = [f for f in arquivos if f.get('name') and f['name'][0].isdigit()]
        
        # Ordena alfabeticamente pelo nome (ex: 01, 02, 03...)
        arquivos_ordenados = sorted(arquivos_filtrados, key=lambda x: x['name'])
        
        return arquivos_ordenados
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Drive: {e}")
        return []

# -----------------------------------------------------------------------------
# 2. CARREGAR O ARQUIVO ESCOLHIDO COMO DATAFRAME
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)
def carregar_dados_web(file_id):
    try:
        creds = service_account.Credentials.from_service_account_info(st.secrets["gcp_service_account"])
        service = build('drive', 'v3', credentials=creds)
        request = service.files().get_media(fileId=file_id)
        file_content = request.execute()
        
        return pd.read_excel(io.BytesIO(file_content))
    except Exception as e:
        st.error(f"Erro ao baixar o arquivo do Drive: {e}")
        return None

# -----------------------------------------------------------------------------
# 3. SUAS FUNÇÕES ORIGINAIS DE CÁLCULO E RELATÓRIOS (Preservadas)
# -----------------------------------------------------------------------------
def processar_matriz_anual(df_filtrado):
    # COLE AQUI A SUA LÓGICA ORIGINAL DA MATRIZ ANUAL (JAN a DEZ)
    pass

def calcular_total_dias(df_selecionados):
    # COLE AQUI A SUA LÓGICA ORIGINAL DE CÁLCULO DE DIAS
    pass

def gerar_relatorio_excel(df_export):
    # COLE AQUI A SUA LÓGICA ORIGINAL DE EXCEL (.xlsx)
    pass

def gerar_relatorio_word(df_export):
    # COLE AQUI A SUA LÓGICA ORIGINAL DE WORD (.docx)
    pass

# -----------------------------------------------------------------------------
# 4. FUNÇÃO PRINCIPAL DE RENDERIZAÇÃO (Chamada pelo app.py)
# -----------------------------------------------------------------------------
def render_pesquisa_remicao():
    st.subheader("🔍 Pesquisa para Remição")
    
    # Busca os arquivos da pasta na nuvem
    lista_arquivos = listar_arquivos_drive(FOLDER_ID)
    
    if not lista_arquivos:
        st.warning("⚠️ Nenhum arquivo iniciado por número foi encontrado na pasta do Google Drive.")
        return
        
    # Cria o dicionário para a caixa de seleção (Nome visível -> ID do arquivo)
    opcoes = {f['name']: f['id'] for f in lista_arquivos}
    
    # Selectbox mostrando apenas os arquivos numerados em ordem alfabética
    arquivo_escolhido = st.selectbox(
        "📁 Selecione a planilha desejada:",
        options=list(opcoes.keys())
    )
    
    if arquivo_escolhido:
        file_id_escolhido = opcoes[arquivo_escolhido]
        
        # Carrega os dados do arquivo selecionado na nuvem
        df_dados = carregar_dados_web(file_id_escolhido)
        
        if df_dados is not None and not df_dados.empty:
            st.success(f"✅ Arquivo **{arquivo_escolhido}** carregado com sucesso!")
            
            # =================================================================
            # AQUI ENTRA TODA A SUA INTERFACE ORIGINAL DE PESQUISA
            # (Filtros por nome/matrícula, tabela de meses, 📌 itens selecionados, etc.)
            # Substitua ou insira abaixo o seu código original usando 'df_dados':
            # =================================================================
            
            # Exemplo de onde aplicar os seus filtros originais:
            # nome_pesquisa = st.text_input("Pesquisar por nome:")
            # df_filtrado = df_dados[df_dados['Nome'].str.contains(nome_pesquisa, na=False)]
            # processar_matriz_anual(df_filtrado)
            
        else:
            st.warning("⚠️ O arquivo selecionado está vazio ou não pôde ser lido.")
