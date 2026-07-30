import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard Geral de Registros", layout="wide")

st.title("📊 Dashboard Completo de Registros e Valores")

@st.cache_data(ttl=60) # Limpa o cache a cada 60 segundos para pegar novos envios
def carregar_dados():
    # Lê a planilha que está na raiz do repositório no GitHub
    df = pd.read_excel('planilha_reorganizada.xlsx')
    
    # Tratamento reforçado da coluna Data (força o formato dia/mês/ano)
    df['data'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
    
    # Tratamento da coluna Valor
    if df['valor'].dtype == 'object':
        df['valor'] = df['valor'].astype(str).str.replace('R$', '', regex=False)
        df['valor'] = df['valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
    df['valor'] = pd.to_numeric(df['valor'], errors='coerce').fillna(0)
    
    # Tratamento da coluna Quantidade
    df['quantidade'] = pd.to_numeric(df['quantidade'], errors='coerce').fillna(0)
    
    # Limpeza e conversão das colunas de texto
    colunas_texto = ['placa', 'funcionario', 'pagamento', 'cliente', 'peça']
    for col in colunas_texto:
        if col in df.columns:
            df[col] = df[col].fillna('').astype(str).str.strip()
        
    return df

df = carregar_dados()

# --- BARRA LATERAL: FILTROS DINÂMICOS ---
st.sidebar.header("🔍 Filtros de Seleção")

# Botão manual para recarregar dados novos se necessário
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# 1. Filtro por Período de Data
datas_validas = df['data'].dropna()

if not datas_validas.empty:
    data_min = datas_validas.min().date()
    data_max = datas_validas.max().date()
    
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

# Helper para gerar listas limpas
def obter_opcoes(df_temp, coluna, opcao_padrao):
    if coluna in df_temp.columns:
        valores = [str(val) for val in df_temp[coluna].unique() if pd.notnull(val) and str(val).strip() not in ['', 'nan', 'None']]
        return [opcao_padrao] + sorted(list(set(valores)))
    return [opcao_padrao]

# 3. Filtros Selecionáveis
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

# --- PAINEL DE MÉTRICAS PRINCIPAIS ---
col1, col2, col3 = st.columns(3)

total_registros = len(df_filtrado)
qtd_pecas = df_filtrado['quantidade'].sum()
valor_total = df_filtrado['valor'].sum()

with col1:
    st.metric(label="📋 Linhas/Ocorrências", value=total_registros)

with col2:
    st.metric(label="🔢 Total de Peças", value=int(qtd_pecas))

with col3:
    st.metric(label="💰 Valor Total do Filtro", value=f"R$ {valor_total:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.'))

st.markdown("---")

# --- ANÁLISE DOS ITENS MAIS VENDIDOS / RETIRADOS ---
st.subheader("🏆 Análise de Peças e Itens no Período")

if not df_filtrado.empty and 'peça' in df_filtrado.columns:
    # Agrupa por peça e calcula a quantidade e valor total
    resumo_pecas = (
        df_filtrado.groupby('peça')
        .agg(
            Quantidade_Total=('quantidade', 'sum'),
            Valor_Total=('valor', 'sum')
        )
        .reset_index()
    )

    # Organização em Abas
    aba_grafico, aba_ranking, aba_registros = st.tabs(["📊 Gráfico Top 10 (por Qtd)", "📋 Ranking Completo (por Valor R$)", "📑 Todos os Registros Filtrados"])

    with aba_grafico:
        top_10 = resumo_pecas.sort_values(by='Quantidade_Total', ascending=False).head(10).sort_values(by='Quantidade_Total', ascending=True)
        
        fig = px.bar(
            top_10, 
            x='Quantidade_Total', 
            y='peça', 
            orientation='h',
            text='Quantidade_Total',
            title="Top 10 Peças Mais Retiradas (por Quantidade)",
            labels={'Quantidade_Total': 'Quantidade Retirada', 'peça': 'Peça / Item'}
        )
        fig.update_traces(textposition='outside', marker_color='#1f77b4')
        fig.update_layout(height=450, margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig, use_container_width=True)

    with aba_ranking:
        resumo_ranking_valor = resumo_pecas.sort_values(by='Valor_Total', ascending=False).copy()
        
        resumo_ranking_valor['Valor_Total'] = resumo_ranking_valor['Valor_Total'].apply(
            lambda v: f"R$ {v:,.2f}".replace(',', 'v').replace('.', ',').replace('v', '.')
        )
        resumo_ranking_valor.columns = ['Peça / Item', 'Quantidade Vendida/Retirada', 'Valor Total Acumulado (R$)']
        
        st.dataframe(resumo_ranking_valor, use_container_width=True, hide_index=True)

    with aba_registros:
        st.dataframe(df_filtrado, use_container_width=True)

else:
    st.info("Nenhum dado encontrado para gerar a análise de itens com os filtros selecionados.")
