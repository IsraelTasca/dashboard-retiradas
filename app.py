import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard Geral de Registros", layout="wide")

st.title("📊 Dashboard Completo de Registros e Valores")

@st.cache_data
def carregar_dados():
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
    
    # Limpeza de texto
    colunas_texto = df.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df[col] = df[col].astype(str).str.strip()
        
    return df

df = carregar_dados()

# --- BARRA LATERAL: FILTROS DINÂMICOS ---
st.sidebar.header("🔍 Filtros de Seleção")

# 1. Filtro de Período
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

# 3. Filtros Selecionáveis
placas = ["Todas"] + sorted([p for p in df_filtrado['placa'].unique() if p != 'nan'])
placa_sel = st.sidebar.selectbox("Placa", placas)

funcionarios = ["Todos"] + sorted([f for f in df_filtrado['funcionario'].unique() if f != 'nan'])
func_sel = st.sidebar.selectbox("Funcionário", funcionarios)

pagamentos = ["Todos"] + sorted([p for p in df_filtrado['pagamento'].unique() if p != 'nan'])
pag_sel = st.sidebar.selectbox("Forma de Pagamento", pagamentos)

clientes = ["Todos"] + sorted([c for c in df_filtrado['cliente'].unique() if c != 'nan'])
cli_sel = st.sidebar.selectbox("Cliente", clientes)

if placa_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado['placa'] == placa_sel]

if func_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['funcionario'] == func_sel]

if pag_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['pagamento'] == pag_sel]

if cli_sel != "Todos":
    df_filtrado = df_filtrado[df_filtrado['cliente'] == cli_sel]

# --- PAINEL PRINCIPAL ---
col1, col2, col3 = st.columns(3)

total_registros = len(df_filtrado)
qtd_pecas = df_filtrado['quantidade'].sum()
valor_total = df_filtrado['valor'].sum()

with col1:
    st.metric(label="📋 Linhas/Ocorrências", value=total_registros)

with col2:
    st.metric(label="🔢 Total de Peças", value=int(qtd_pecas))

with col3:
    st.metric(label="💰 Valor Total", value=f"R$ {valor_total:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.'))

st.markdown("---")
st.subheader("📋 Tabela de Registros Filtrados")
st.dataframe(df_filtrado, use_container_width=True)
