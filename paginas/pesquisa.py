import streamlit as st
import pandas as pd
import io

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Pesquisa para Remição",
    page_icon="🔍",
    layout="wide"
)

# -----------------------------------------------------------------------------
# 2. INICIALIZAÇÃO DO SESSION STATE
# -----------------------------------------------------------------------------
if "pesquisa_df" not in st.session_state:
    st.session_state["pesquisa_df"] = None

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

if "executar_config" not in st.session_state:
    st.session_state["executar_config"] = False

if "rolar_apos_upload" not in st.session_state:
    st.session_state["rolar_apos_upload"] = False


# -----------------------------------------------------------------------------
# 3. FUNÇÕES AUXILIARES
# -----------------------------------------------------------------------------
def conv_num(val):
    """Converte valores de forma segura para float."""
    try:
        if pd.isna(val):
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        val_str = str(val).replace(",", ".").strip()
        return float(val_str)
    except Exception:
        return 0.0


# -----------------------------------------------------------------------------
# 4. CABEÇALHO DA APLICAÇÃO
# -----------------------------------------------------------------------------
st.title("🔍 Opção 3: Pesquisa para Remição")
st.markdown("Carregue as bases de dados para consolidar, filtrar e exportar relatórios de remição por interno.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. SEÇÃO DE UPLOAD DE ARQUIVOS
# -----------------------------------------------------------------------------
st.subheader("📁 Upload de Arquivos (Excel / CSV)")

uploaded_files = st.file_uploader(
    "Selecione uma ou mais planilhas de remição:",
    type=["xlsx", "xls", "csv"],
    accept_multiple_files=True,
    key=f"uploader_{st.session_state['uploader_key']}"
)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        try:
            if file.name.endswith(".csv"):
                df_temp = pd.read_csv(file)
            else:
                df_temp = pd.read_excel(file)
            
            # Normalizar nomes das colunas
            df_temp.columns = [str(col).strip().upper() for col in df_temp.columns]
            dfs.append(df_temp)
        except Exception as e:
            st.error(f"Erro ao ler o arquivo {file.name}: {e}")

    if dfs:
        df_consolidado = pd.concat(dfs, ignore_index=True)
        st.session_state["pesquisa_df"] = df_consolidado
        st.success(f"✅ {len(uploaded_files)} arquivo(s) carregado(s) com sucesso! Total de registros: {len(df_consolidado)}")

# -----------------------------------------------------------------------------
# 6. PROCESSAMENTO, FILTROS E EXIBIÇÃO
# -----------------------------------------------------------------------------
if st.session_state["pesquisa_df"] is not None and not st.session_state["pesquisa_df"].empty:
    df_main = st.session_state["pesquisa_df"].copy()

    # Garantir a existência de colunas essenciais
    cols_requeridas = ["NOME", "ORGANIZACAO", "FUNCAO", "SAIDA/STATUS", "PREV", "REAL", "CATEGORIA"]
    for col in cols_requeridas:
        if col not in df_main.columns:
            df_main[col] = "N/I"

    st.markdown("---")
    st.subheader("🔎 Filtros de Pesquisa")

    col_f1, col_f2, col_f3 = st.columns(3)

    with col_f1:
        busca_nome = st.text_input("Filtrar por Nome do Interno:", value="", placeholder="Digite o nome...")
    
    with col_f2:
        categorias = ["TODAS"] + sorted(list(df_main["CATEGORIA"].astype(str).unique()))
        cat_selecionada = st.selectbox("Grupo / Categoria de Remuneração:", options=categorias)

    with col_f3:
        status_list = ["TODOS"] + sorted(list(df_main["SAIDA/STATUS"].astype(str).unique()))
        status_selecionado = st.selectbox("Status / Saída:", options=status_list)

    # Aplicação dos Filtros
    df_filtrado = df_main.copy()

    if busca_nome:
        df_filtrado = df_filtrado[df_filtrado["NOME"].astype(str).str.contains(busca_nome, case=False, na=False)]

    if cat_selecionada != "TODAS":
        df_filtrado = df_filtrado[df_filtrado["CATEGORIA"].astype(str) == cat_selecionada]

    if status_selecionado != "TODOS":
        df_filtrado = df_filtrado[df_filtrado["SAIDA/STATUS"].astype(str) == status_selecionado]

    st.markdown("---")

    if not df_filtrado.empty:
        # Coluna de seleção
        if "SELECIONAR?" not in df_filtrado.columns:
            df_filtrado.insert(0, "SELECIONAR?", True)

        # Agrupamento por Categoria
        grupos = df_filtrado.groupby("CATEGORIA")

        todos_dados_exportacao = []

        st.subheader("📋 Resultados da Pesquisa por Interno")

        for cat_key, df_grupo in grupos:
            st.markdown(f"### 🏷️ Categoria / Grupo: **{cat_key}**")
            
            # Subagrupamento por Interno
            internos = df_grupo.groupby("NOME")

            for nome_interno, df_nome_sel in internos:
                # Metadados do primeiro registro
                primeiro_registro = df_nome_sel.iloc[0]
                organiz_val = primeiro_registro.get("ORGANIZACAO", "N/I")
                funcao_val = primeiro_registro.get("FUNCAO", "N/I")
                saida_val = primeiro_registro.get("SAIDA/STATUS", "N/I")

                # Cálculo das somatórias previstas e realizadas
                soma_prev = sum(conv_num(v) for v in df_nome_sel["PREV"]) if "PREV" in df_nome_sel.columns else 0.0
                soma_real = sum(conv_num(v) for v in df_nome_sel["REAL"]) if "REAL" in df_nome_sel.columns else 0.0

                # Card expansível por interno
                with st.expander(f"👤 Interno: **{nome_interno}** | Total Realizado: **{int(round(soma_real))}** dia(s)/hora(s)", expanded=True):
                    col_inf1, col_inf2, col_inf3, col_inf4 = st.columns(4)
                    with col_inf1:
                        st.markdown(f"**Organização:** {organiz_val if pd.notna(organiz_val) else 'N/I'}")
                    with col_inf2:
                        st.markdown(f"**Função:** {funcao_val if pd.notna(funcao_val) else 'N/I'}")
                    with col_inf3:
                        st.markdown(f"**Saída/Status:** {saida_val if pd.notna(saida_val) else 'N/I'}")
                    with col_inf4:
                        st.metric("Total Dias (REAL)", f"{int(round(soma_real))}")

                    st.dataframe(
                        df_nome_sel.drop(columns=["SELECIONAR?"], errors="ignore"),
                        use_container_width=True,
                        hide_index=True
                    )

                # Acumulador para exportação
                for _, row_sel in df_nome_sel.iterrows():
                    item_exp = row_sel.to_dict()
                    item_exp["Grupo Remuneração"] = cat_key
                    todos_dados_exportacao.append(item_exp)

        # -----------------------------------------------------------------
        # 7. PAINEL DE EXPORTAÇÃO E AÇÕES
        # -----------------------------------------------------------------
        st.markdown("---")
        st.subheader("📥 Exportação e Ações Globais")

        col_exp1, col_exp2, col_exp3 = st.columns(3)

        with col_exp1:
            if todos_dados_exportacao:
                df_export = pd.DataFrame(todos_dados_exportacao)
                df_export = df_export.drop(columns=["SELECIONAR?"], errors="ignore")

                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    df_export.to_excel(writer, index=False, sheet_name='Pesquisa_Remicao')
                excel_data = output.getvalue()

                st.download_button(
                    label="📥 Baixar Selecionados (.XLSX)",
                    data=excel_data,
                    file_name="pesquisa_remicao_selecionados.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    type="primary",
                    use_container_width=True
                )
            else:
                st.info("Marque pelo menos um registro acima para habilitar o download.")

        with col_exp2:
            if st.session_state.get("pesquisa_df") is not None:
                output_all = io.BytesIO()
                with pd.ExcelWriter(output_all, engine='xlsxwriter') as writer:
                    st.session_state["pesquisa_df"].to_excel(writer, index=False, sheet_name='Consolidado_Geral')
                excel_all_data = output_all.getvalue()

                st.download_button(
                    label="📦 Baixar Base Consolidada Total (.XLSX)",
                    data=excel_all_data,
                    file_name="consolidado_pesquisa_remicao.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )

        with col_exp3:
            if st.button("🗑️ Limpar Tudo e Reiniciar", key="btn_limpar_pesquisa", type="secondary", use_container_width=True):
                st.session_state["pesquisa_df"] = None
                st.session_state["executar_config"] = False
                st.session_state["rolar_apos_upload"] = False
                st.session_state["uploader_key"] += 1
                st.rerun()

    else:
        st.warning("Nenhum registro encontrado para os critérios de busca/filtro informados.")
else:
    st.info("Aguardando o carregamento dos arquivos acima para exibir a pesquisa.")
