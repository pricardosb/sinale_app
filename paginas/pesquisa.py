import streamlit as st
import pandas as pd
import io

# -----------------------------------------------------------------------------
# FUNÇÃO PARA FORMATAR LINKS PÚBLICOS DE ARMAZENAMENTO EM NUVEM
# -----------------------------------------------------------------------------
def formatar_url_download_direto(url: str) -> str:
    """Converte links de visualização do Google Drive, GitHub ou Dropbox em links de download direto."""
    url = url.strip()
    
    # 1. Google Drive
    if "drive.google.com" in url:
        if "/file/d/" in url:
            file_id = url.split("/file/d/")[1].split("/")[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        elif "id=" in url:
            file_id = url.split("id=")[1].split("&")[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
            
    # 2. GitHub (Converte link de visualização do código para 'Raw')
    elif "github.com" in url and "/raw/" not in url:
        return url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
        
    # 3. Dropbox
    elif "dropbox.com" in url:
        return url.replace("dl=0", "dl=1")
        
    return url

# -----------------------------------------------------------------------------
# CARREGAMENTO DOS DADOS COM TRATAMENTO DE ERRO
# -----------------------------------------------------------------------------
@st.cache_data(ttl=600)  # Atualiza os dados a cada 10 minutos
def carregar_dados_web(url_original):
    url_direta = formatar_url_download_direto(url_original)
    try:
        # Se for um arquivo Excel
        if ".xlsx" in url_original.lower() or ".xls" in url_original.lower() or "drive.google.com" in url_original:
            return pd.read_excel(url_direta)
        # Se for um arquivo CSV
        else:
            return pd.read_csv(url_direta)
    except Exception as e:
        st.error(f"⚠️ Erro ao carregar o arquivo da Web. Verifique a URL fornecida.\n\nDetalhes do erro: {e}")
        return None

# =============================================================================
# COLOQUE AQUI A SUA URL REAL DE ONDE A PLANILHA ESTÁ HOSPEDADA:
# =============================================================================
URL_SUA_PLANILHA = "https://drive.google.com/file/d/SEU_ID_AQUI/view?usp=sharing"

# Executa o carregamento
df_dados = carregar_dados_web(URL_SUA_PLANILHA)
