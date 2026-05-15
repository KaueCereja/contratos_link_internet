import streamlit as st
import pandas as pd
import re

st.set_page_config(page_title="Links e Internet", layout="wide")

st.markdown("""
## 📡 Consulta de Links de Dados e Internet
""")

# ==================== CARREGAMENTO DE DADOS ====================
@st.cache_data(ttl=3600)
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vStCsK-I9n6aQ6argn2xcQ1jIe5BCcvHrG5PNmq7xd13dd6i5iZovnR8ahCOzUQZztC8DlT4vYAZyRf/pub?output=csv"
    
    try:
        df = pd.read_csv(url)
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar do Google Sheets: {e}")
        try:
            df = pd.read_csv("internet-link-CT-14-05-2026 - servicos-contratos.csv", encoding='utf-8')
        except:
            st.error("❌ Não foi possível carregar os dados.")
            return pd.DataFrame()
    
    df.columns = [col.strip() for col in df.columns]
    
    # ===== TRATAMENTO DA COLUNA SIGLA - PRESERVANDO TODOS OS REGISTROS =====
    if 'SIGLA' in df.columns:
        # Limpar espaços e converter para maiúsculas (apenas onde há valor)
        df['SIGLA'] = df['SIGLA'].astype(str).str.strip().str.upper()
        df['SIGLA'] = df['SIGLA'].replace(['NAN', 'NONE', 'N/A', 'nan', 'None'], '')
        df['SIGLA'] = df['SIGLA'].fillna('')
        
        # ===== NOVO: Criar uma SIGLA alternativa usando o CLIENTE =====
        # Para registros sem SIGLA, extrair do nome do cliente
        def extrair_sigla_do_cliente(cliente):
            if pd.isna(cliente) or not isinstance(cliente, str):
                return ''
            # Tentar extrair sigla do nome (ex: "FUNDACAO PROPAZ" -> "FUNDPROPAZ")
            palavras = cliente.split()
            if len(palavras) >= 2:
                # Pega primeiras letras ou abreviação comum
                sigla = ''.join([p[0] for p in palavras if len(p) > 2])[:10]
                return sigla if sigla else palavras[0][:8]
            return cliente[:8] if len(cliente) > 8 else cliente
        
        # Preencher SIGLAS vazias com siglas derivadas do CLIENTE
        mask_sem_sigla = df['SIGLA'] == ''
        if mask_sem_sigla.any():
            df.loc[mask_sem_sigla, 'SIGLA'] = df.loc[mask_sem_sigla, 'CLIENTE'].apply(extrair_sigla_do_cliente)
    
    # Converter valores monetários
    money_cols = ['VALOR UNITARIO', 'VALOR UNITARIO ATUAL', 'VALOR ANUAL', 'VALOR GLOBAL']
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('R$ ', '').str.replace('.', '').str.replace(',', '.').str.replace('"', '')
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # Converter datas
    date_cols = ['DATA INICIO CT', 'DATA FIM CT', 'DATA INICIO ADITIVO', 'DATA FIM ADITIVO']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], format='%d/%m/%Y', errors='coerce')
    
    return df

df = load_data()

if df.empty:
    st.stop()

# ===== ESTATÍSTICAS DE DIAGNÓSTICO =====
total_registros = len(df)
registros_com_sigla = len(df[df['SIGLA'] != ''])
registros_sem_sigla = total_registros - registros_com_sigla

# ==================== SIDEBAR ====================
with st.sidebar:
    st.markdown("# 🎯 Filtros")
    
    # Mostrar estatísticas
    st.caption(f"📊 Total: {total_registros} registros")
    if registros_sem_sigla > 0:
        st.caption(f"⚠️ {registros_sem_sigla} registros sem SIGLA original (preenchidos automaticamente)")
    
    if st.button("🔄 Limpar Todos os Filtros", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    filtros = {}
    
    # 1. SIGLA - INCLUINDO TODOS OS REGISTROS
    siglas_validas = sorted([s for s in df['SIGLA'].unique() if s and s != ''])
    
    if siglas_validas:
        sigla_sel = st.multiselect(
            "🏢 Cliente (SIGLA)",
            options=siglas_validas,
            help="Selecione uma ou mais SIGLAS. Registros sem SIGLA foram preenchidos automaticamente."
        )
        if sigla_sel:
            filtros['SIGLA'] = sigla_sel
    
    # 2. MUNICÍPIO
    municipios = sorted(df['MUNICIPIO'].dropna().unique())
    municipio_sel = st.multiselect("📍 Município", options=municipios)
    if municipio_sel:
        filtros['MUNICIPIO'] = municipio_sel
    
    # 3. REGIÃO
    regioes = sorted(df['REGIÃO'].dropna().unique())
    regiao_sel = st.multiselect("🗺️ Região", options=regioes)
    if regiao_sel:
        filtros['REGIÃO'] = regiao_sel
    
    # 4. SERVIÇO
    servicos = sorted(df['SERVICO'].dropna().unique())
    servico_sel = st.multiselect("🔌 Serviço", options=servicos)
    if servico_sel:
        filtros['SERVICO'] = servico_sel
    
    # 5. STATUS DO SERVIÇO
    status_serv = sorted(df['STATUS SERVICO'].dropna().unique())
    status_sel = st.multiselect("⚡ Status do Serviço", options=status_serv)
    if status_sel:
        filtros['STATUS SERVICO'] = status_sel
    
    # 6. STATUS DO CONTRATO
    status_cont = sorted(df['STATUS CONTRATO'].dropna().unique())
    status_cont_sel = st.multiselect("📄 Status do Contrato", options=status_cont)
    if status_cont_sel:
        filtros['STATUS CONTRATO'] = status_cont_sel
    
    st.divider()
    

# ==================== APLICAÇÃO DOS FILTROS ====================
df_filtrado = df.copy()

if 'SIGLA' in filtros:
    df_filtrado = df_filtrado[df_filtrado['SIGLA'].isin(filtros['SIGLA'])]

if 'MUNICIPIO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['MUNICIPIO'].isin(filtros['MUNICIPIO'])]

if 'REGIÃO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['REGIÃO'].isin(filtros['REGIÃO'])]

if 'SERVICO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['SERVICO'].isin(filtros['SERVICO'])]

if 'STATUS SERVICO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['STATUS SERVICO'].isin(filtros['STATUS SERVICO'])]

if 'STATUS CONTRATO' in filtros:
    df_filtrado = df_filtrado[df_filtrado['STATUS CONTRATO'].isin(filtros['STATUS CONTRATO'])]


# ==================== EXIBIÇÃO ====================
st.dataframe(
    df_filtrado,
    use_container_width=True,
    height=min(600, len(df_filtrado) * 35 + 50)
)

if len(df_filtrado) > 0:
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Baixar CSV",
        csv,
        "dados_filtrados.csv",
        "text/csv",
        use_container_width=True
    )