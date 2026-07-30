import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Geral de Registros", layout="wide")

st.title("📊 Dashboard Completo de Registros e Valores")

@st.cache_data
def carregar_dados():
    # Lê a planilha que está na raiz do repositório no GitHub
    df = pd.read_excel('planilha_reorganizada.xlsx')
    
    # Tratamento da coluna Data
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    
    # Tratamento da coluna Valor
    if df['valor'].dtype == 'object':
        df['valor'] = df['valor'].astype(str).str.replace('R$', '', regex=False)
        df['valor'] = df['valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Tratamento da coluna Quantidade
    df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
    
    # Limpeza e conversão das colunas de texto para evitar erros no sorted()
    colunas_texto = ['placa', 'funcionario', 'pagamento', 'cliente', 'peça']
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
        
    return df

df = carregar_dados()

# --- BARRA LATERAL: FILTROS DINÂMICOS ---
st.sidebar.header("🔍 Filtros de Seleção")

# 1. Filtro por Período de Data
data_min = df['data'].min().date() if not df['data'].isnull().all() else None
data_max = df['data'].max().date() if not df['data'].isnull().all() else None

if data_min and data_max:
    data_inicio, data_fim = st.sidebar.date_input(
        "📅 Período",
        value=(data_min, data_max),
        min_value=data_min,
        max_value=data_max
    )
else:
    data_inicio, data_fim = None, None

# Aplicação do Filtro de Data
df_filtrado = df.copy()
if data_inicio and data_fim:
    df_filtrado = df_filtrado[
        (df_filtrado['data'].dt.date >= data_inicio) & 
        (df_filtrado['data'].dt.date <= data_fim)
    ]

st.sidebar.markdown("---")

# 2. Busca Rápida de Texto
termo_busca = st.sidebar.text_input("🔎 Pesquisa Geral (qualquer termo):", "")

if termo_busca:
    mascara = df_filtrado.astype(str).apply(
        lambda col: col.str.contains(termo_busca, case=False, na=False)
    ).any(axis=1)
    df_filtrado = df_filtrado[mascara]

st.sidebar.markdown("---")
st.sidebar.subheader("Filtre por Coluna Específica")

# Helper para gerar listas limpas sem valores nulos/vazios
def obter_opcoes(df_temp, coluna, opcao_padrao):
    if coluna in df_temp.columns:
        valores = [str(val) for val in df_temp[coluna].unique() if pd.notnull(val) and str(val).strip() not in ['', 'nan', 'None']]
        return [opcao_padrao] + sorted(list(set(valores)))
    return [opcao_padrao]

# 3. Filtros Selecionáveis Seguros
placa_sel = st.sidebar.selectbox("Placa", obter_opcoes(df_filtrado, 'placa', "Todas"))
func_sel = st.sidebar.selectbox("Funcionário", obter_opcoes(df_filtrado, 'funcionario', "Todos"))
pag_sel = st.sidebar.selectbox("Forma de Pagamento", obter_opcoes(df_filtrado, 'pagamento', "Todos"))
cli_sel = st.sidebar.selectbox("Cliente", obter_opcoes(df_filtrado, 'cliente', "Todos"))

# Aplicação dos Filtros
if placa_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['placa'] == placa_sel]

if func_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['funcionario'] == func_sel]

if pag_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['pagamento'] == pag_sel]

if cli_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['cliente'] == cli_sel]

# --- PAINEL DE MÉTRICAS E RESULTADOS ---
col1, col2, col3 = st.columns(3)

total_registros = len(df_filtrado)
qtd_pecas = df_filtrado['quantidade'].sum()
valor_total = df_filtrado['valor'].sum()

with col1:
    st.metric(label="📋 Linhas/Ocorrências Encontradas", value=total_registros)

with col2:
    st.metric(label="🔢 Total de Peças/Quantidade", value=int(qtd_pecas))

with col3:
    st.metric(label="💰 Valor Total do Filtro", value=f"R$ {valor_total:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.'))

st.markdown("---")

# --- TABELA INTERATIVA DE REGISTROS ---
st.subheader("📋 Tabela de Registros Filtrados")
st.dataframe(df_filtrado, use_container_width=True)
