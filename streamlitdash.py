import streamlit as st
import pandas as pd
import plotly.express as px
from tratamento import tratamento_dados

# Carregando os dados
df = tratamento_dados()

# Configuração da página
st.set_page_config(page_title="Dashboard de Chamados de Serviços Urbanos", layout="wide")

# Aplicar tema claro com fundo branco
st.markdown(
    """
    <style>
    .main {
        background-color: #ffffff;
        color: #000000;
    }
    .sidebar .sidebar-content {
        background-color: #f0f0f0;
        color: #000000;
    }
    h1, h2, h3, h4, h5, h6 {
        color: #000000;
    }
    .stMetricLabel, .stMetricValue {
        color: #000000 !important;
    }
    .stSelectbox label, .stMultiSelect label {
        color: #000000;
    }
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff;
    }
    .stTabs [data-baseweb="tab"] {
        color: #000000;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Título principal
st.title("Análise de Chamados - EMLURB 2024")

# Sidebar para filtros
st.sidebar.header("Filtros")
zonas = st.sidebar.multiselect("Zona", options=df['ZONA'].unique(), default=df['ZONA'].unique())
meses = st.sidebar.multiselect("Mês", options=df['MES'].unique(), default=df['MES'].unique())
situacoes = st.sidebar.multiselect("Situação", options=df['SITUACAO'].unique(), default=df['SITUACAO'].unique())

# Tabs para grupos de serviço + TOTAL
grupos_unicos = sorted(df['GRUPOSERVICO_DESCRICAO'].unique())
tab_names = ["TOTAL"] + grupos_unicos
tabs = st.tabs(tab_names)

# Dicionário de situações com cores ajustadas
situacoes_order = {
    1: {"nome": "Cadastrada", "cor": "#808080"},  # Cinza
    2: {"nome": "Preparação", "cor": "#4682b4"},  # Azul
    3: {"nome": "Execução", "cor": "#ffa500"},    # Laranja
    4: {"nome": "Pendencia", "cor": "#ff4040"},   # Vermelho
    5: {"nome": "Atendida", "cor": "#32cd32"},    # Verde
    6: {"nome": "Fiscalização", "cor": "#9370db"} # Roxo
}

# Iterar sobre nomes e tabs juntos
for tab_name, tab in zip(tab_names, tabs):
    with tab:
        grupo = tab_name if tab_name != "TOTAL" else None
        
        # Filtragem inicial por grupo (se aplicável), zonas, meses e situações
        if grupo:
            df_grupo = df[df['GRUPOSERVICO_DESCRICAO'] == grupo]
        else:
            df_grupo = df.copy()
        
        filtered_df = df_grupo[
            df_grupo['ZONA'].isin(zonas) &
            df_grupo['MES'].isin(meses) &
            df_grupo['SITUACAO'].isin(situacoes)
        ]
        
        # Bloco 1: Visão Geral
        st.header("1 - Visão Geral")
        
        # KPIs principais
        col1, col2, col3 = st.columns(3)
        total_chamados = len(filtered_df)
        with col1:
            st.metric("Total de Chamados", f"{total_chamados:,.0f}".replace(",", "."))
        
        # % Atendida (incluindo Fiscalização)
        percent_atendida = ((filtered_df['SITUACAO'] == 'ATENDIDA') | (filtered_df['SITUACAO'] == 'FISCALIZACAO')).mean() * 100 if total_chamados > 0 else 0
        with col2:
            st.metric("% Atendida", f"{percent_atendida:.0f}%")
        
        # Tempo médio apenas para ATENDIDA e FISCALIZACAO
        att_fisc_df = filtered_df[filtered_df['SITUACAO'].isin(['ATENDIDA', 'FISCALIZACAO'])]
        tempo_medio = att_fisc_df['DIFERENCA_DIAS'].mean() if not att_fisc_df.empty else 0
        with col3:
            st.metric("Tempo Médio de Atendimento (dias)", f"{tempo_medio:.0f}")
        
        # Bloco 2: Eficiência Operacional
        st.header("2 - Eficiência Operacional")
        
        # % Atendido por Mês
        st.subheader("% ATENDIDO (MÊS)")
        all_meses = pd.DataFrame({'MES': range(1, 13)})
        percent_por_mes = filtered_df.groupby('MES').agg(
            {'SITUACAO': lambda x: ((x == 'ATENDIDA') | (x == 'FISCALIZACAO')).mean() * 100}
        ).reset_index().rename(columns={'SITUACAO': '% Atendida'})
        percent_por_mes['% Atendida'] = percent_por_mes['% Atendida'].astype('float64')
        percent_por_mes = all_meses.merge(percent_por_mes, on='MES', how='left').fillna({'% Atendida': 0})
        fig_percent = px.bar(percent_por_mes, x='MES', y='% Atendida', color_discrete_sequence=['#4682b4'])
        fig_percent.update_layout(
            xaxis={'tickmode': 'array', 'tickvals': list(range(1, 13)), 'title': {'text': 'Mês', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            yaxis={'range': [0, 100], 'title': {'text': '% Atendida', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font={'color': 'black'}
        )
        st.plotly_chart(fig_percent, use_container_width=True, key=f"percent_por_mes_{tab_names.index(tab_name)}_{tab_name}")
        
        # Top 10 Serviços
        st.subheader("TOP 10 SERVIÇOS (QTD)")
        chamados_por_servico = filtered_df.groupby(['GRUPOSERVICO_DESCRICAO', 'SERVICO_DESCRICAO']).size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False).head(10)
        fig_servico = px.bar(chamados_por_servico, x='Quantidade', y='SERVICO_DESCRICAO', color='GRUPOSERVICO_DESCRICAO', orientation='h', color_discrete_sequence=px.colors.sequential.Blues_r)
        fig_servico.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': {'text': '', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            xaxis={'title': {'text': '', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font={'color': 'black'}
        )
        st.plotly_chart(fig_servico, use_container_width=True, key=f"servicos_{tab_names.index(tab_name)}_{tab_name}")
        
        # Bloco 3: Distribuição Geográfica
        st.header("3 - Distribuição Geográfica")
        
        # Chamados por Zona
        st.subheader("CHAMADOS POR ZONA")
        col_zona1, col_zona2 = st.columns([1, 2])
        with col_zona2:
            chamados_por_zona = filtered_df.groupby('ZONA').size().reset_index(name='Quantidade')
            fig_zona = px.pie(chamados_por_zona, values='Quantidade', names='ZONA', color_discrete_sequence=px.colors.sequential.Blues_r)
            fig_zona.update_layout(
                legend=dict(font=dict(size=18, color='black'), x=1.2, y=0.5, xanchor='left', yanchor='middle'),
                showlegend=True,
                paper_bgcolor='white',
                plot_bgcolor='white',
                font={'color': 'black'}
            )
            st.plotly_chart(fig_zona, use_container_width=True, key=f"zona_{tab_names.index(tab_name)}_{tab_name}")
        
        # Top 10 Bairros
        st.subheader("TOP 10 BAIRROS (QTD)")
        chamados_por_bairro = filtered_df.groupby('BAIRRO').size().reset_index(name='Quantidade').sort_values('Quantidade', ascending=False).head(10)
        fig_bairro = px.bar(chamados_por_bairro, x='Quantidade', y='BAIRRO', orientation='h', color_discrete_sequence=['#4682b4'])
        fig_bairro.update_layout(
            yaxis={'categoryorder':'total ascending', 'title': {'text': '', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            xaxis={'title': {'text': '', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font={'color': 'black'}
        )
        st.plotly_chart(fig_bairro, use_container_width=True, key=f"bairro_{tab_names.index(tab_name)}_{tab_name}")
        
        # Bloco 4: Sazonalidade e Tendências
        st.header("4 - Sazonalidade e Tendências")
        
        # Chamados por Mês
        st.subheader("CHAMADOS POR MÊS (SAZONALIDADE)")
        all_meses = pd.DataFrame({'MES': range(1, 13)})
        chamados_por_mes = filtered_df.groupby('MES').size().reset_index(name='Quantidade')
        chamados_por_mes = all_meses.merge(chamados_por_mes, on='MES', how='left').fillna({'Quantidade': 0})
        fig_mes = px.line(chamados_por_mes, x='MES', y='Quantidade', markers=True, color_discrete_sequence=['#4682b4'])
        fig_mes.update_layout(
            xaxis={'tickmode': 'array', 'tickvals': list(range(1, 13)), 'title': {'text': 'Mês', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            yaxis={'range': [0, chamados_por_mes['Quantidade'].max() * 1.1], 'title': {'text': 'Quantidade de Chamados', 'font': {'color': 'black'}}, 'tickfont': {'color': 'black'}},
            showlegend=False,
            paper_bgcolor='white',
            plot_bgcolor='white',
            font={'color': 'black'}
        )
        fig_mes.update_traces(textposition='top center')
        st.plotly_chart(fig_mes, use_container_width=True, key=f"mes_{tab_names.index(tab_name)}_{tab_name}")