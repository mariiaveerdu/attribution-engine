import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE PÁGINA
st.set_page_config(page_title="Marketing Dashboard Pro", layout="wide", page_icon="📈")

# 2. ESTILO CSS CUSTOM (Sin cajas negras, diseño más "Soft")
st.markdown("""
    <style>
    /* Fondo general */
    .main { background-color: #0f1115; color: #e1e1e1; }
    
    /* Títulos de sección */
    h2 { color: #808495; font-size: 1.2rem !important; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Estilo de las métricas (limpio, sin recuadro pesado) */
    [data-testid="stMetric"] {
        border-bottom: 2px solid #2d3139;
        padding: 10px 0px;
    }
    
    /* Quitar bordes de tablas */
    .stDataFrame { border: none !important; }
    </style>
    """, unsafe_allow_html=True)

@st.cache_data(ttl=600)
def get_data(md_token):
    try:
        con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
        df = con.sql("SELECT * FROM detective_ventas.main.fct_attribute_last_click").df()
        con.close()
        df.columns = [c.lower() for c in df.columns]
        df['converted_at'] = pd.to_datetime(df['converted_at'])
        df['fecha_dia'] = df['converted_at'].dt.date
        df['dia_semana'] = df['converted_at'].dt.day_name()
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.title("⚙️ Filtros")
    token = st.secrets.get("MOTHERDUCK_TOKEN") or st.text_input("MotherDuck Token", type="password")
    if not token: st.stop()
    st.markdown("---")

df_raw = get_data(token)

if df_raw is not None:
    # Filtros de canal
    canales = st.sidebar.multiselect("Canales", sorted(df_raw['winning_channel'].unique()), default=df_raw['winning_channel'].unique())
    df = df_raw[df_raw['winning_channel'].isin(canales)]

    # --- HEADER ---
    st.title("💎 Marketing Intelligence | Command Center")
    st.caption(f"Visualizando datos desde {df['fecha_dia'].min()} hasta {df['fecha_dia'].max()}")
    
    # --- SECCIÓN 1: KPIs ---
    st.markdown("## Resumen Ejecutivo")
    k1, k2, k3, k4 = st.columns(4)
    rev_total = df['revenue_amount'].sum()
    conv_total = len(df)
    aov = rev_total / conv_total if conv_total > 0 else 0
    
    k1.metric("Revenue Total", f"{rev_total:,.0f}€")
    k2.metric("Conversiones", f"{conv_total:,}")
    k3.metric("Ticket Medio (AOV)", f"{aov:,.2f}€")
    k4.metric("Mix de Canales", f"{df['winning_channel'].nunique()}")

    st.markdown("---")

    # --- SECCIÓN 2: TENDENCIAS Y MIX ---
    c1, c2 = st.columns([7, 3])
    
    with c1:
        st.markdown("## Evolución Temporal de Ingresos")
        df_line = df.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
        fig_line = px.line(df_line, x='fecha_dia', y='revenue_amount', color='winning_channel', markers=True, 
                           template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Safe)
        fig_line.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', legend_title="")
        st.plotly_chart(fig_line, use_container_width=True)

    with c2:
        st.markdown("## Share por Canal")
        fig_pie = px.pie(df, values='revenue_amount', names='winning_channel', hole=0.7, 
                         template="plotly_dark", color_discrete_sequence=px.colors.sequential.Aggrnyl)
        fig_pie.update_layout(showlegend=False, plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN 3: COMPORTAMIENTO SEMANAL ---
    st.markdown("## Análisis de Rendimiento por Día")
    orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    df_week = df.groupby(['dia_semana', 'winning_channel'])['revenue_amount'].sum().reset_index()
    # Asegurar el orden de los días en el gráfico
    df_week['dia_semana'] = pd.Categorical(df_week['dia_semana'], categories=orden_dias, ordered=True)
    df_week = df_week.sort_values('dia_semana')

    fig_week = px.bar(df_week, x='dia_semana', y='revenue_amount', color='winning_channel',
                      template="plotly_dark", barmode='group', color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_week.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="")
    st.plotly_chart(fig_week, use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN 4: PARETO Y EFICIENCIA ---
    st.markdown("## Diagnóstico Estratégico")
    col_p1, col_p2 = st.columns(2)

    with col_p1:
        # Pareto de canales
        df_p = df.groupby('winning_channel')['revenue_amount'].sum().sort_values(ascending=False).reset_index()
        df_p['acum'] = (df_p['revenue_amount'].cumsum() / df_p['revenue_amount'].sum()) * 100
        fig_p = go.Figure()
        fig_p.add_trace(go.Bar(x=df_p['winning_channel'], y=df_p['revenue_amount'], name="Revenue", marker_color='#4f8bff'))
        fig_p.add_trace(go.Scatter(x=df_p['winning_channel'], y=df_p['acum'], name="% Acumulado", yaxis="y2", line=dict(color="#00ffcc", width=3)))
        fig_p.update_layout(template="plotly_dark", yaxis2=dict(overlaying='y', side='right', range=[0, 110]), 
                            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', showlegend=False)
        st.plotly_chart(fig_p, use_container_width=True)

    with col_p2:
        # Matriz de Eficiencia (Scatter)
        df_eff = df.groupby('winning_channel').agg({'revenue_amount':['sum', 'mean'], 'winning_channel':'count'}).reset_index()
        df_eff.columns = ['canal', 'total', 'avg', 'count']
        fig_scatter = px.scatter(df_eff, x='count', y='avg', size='total', color='canal', 
                                 template="plotly_dark", size_max=40, color_discrete_sequence=px.colors.qualitative.Vivid)
        fig_scatter.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', xaxis_title="Nº de Ventas", yaxis_title="Ticket Medio (€)")
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # --- SECCIÓN 5: AUDITORÍA ---
    st.markdown("## Auditoría de Transacciones")
    st.dataframe(df.sort_values('converted_at', ascending=False), use_container_width=True)

else:
    st.error("Error al cargar la base de datos.")