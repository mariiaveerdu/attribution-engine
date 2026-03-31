import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN
st.set_page_config(page_title="Marketing Intelligence OS", layout="wide", page_icon="📈")

# Estilo Premium
st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    div[data-testid="stMetric"] {
        background-color: #161b22; border: 1px solid #30363d;
        padding: 15px; border-radius: 12px;
    }
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
        # Extraemos el nombre del día para el análisis semanal
        df['dia_semana'] = df['converted_at'].dt.day_name()
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error en datos: {e}")
        return None

# --- AUTH & FILTROS ---
with st.sidebar:
    st.header("🔑 Acceso")
    token = st.secrets.get("MOTHERDUCK_TOKEN") or st.text_input("Token", type="password")
    if not token: st.stop()

df_raw = get_data(token)

if df_raw is not None:
    canales = st.sidebar.multiselect("Canales", sorted(df_raw['winning_channel'].unique()), default=df_raw['winning_channel'].unique())
    df = df_raw[df_raw['winning_channel'].isin(canales)]

    # --- KPIs ---
    st.title("📈 Marketing Intelligence OS")
    k1, k2, k3 = st.columns(3)
    k1.metric("Revenue Total", f"{df['revenue_amount'].sum():,.0f}€", "+12%")
    k2.metric("Conversiones", f"{len(df):,}", "+5%")
    k3.metric("Ticket Medio", f"{(df['revenue_amount'].sum()/len(df)):,.2f}€" if len(df)>0 else "0€")

    # --- PESTAÑAS ---
    tab1, tab2, tab3 = st.tabs(["📊 Performance", "📅 Análisis Semanal", "🎯 Eficiencia (Pareto)"])

    with tab1:
        c1, c2 = st.columns([7, 3])
        with c1:
            st.subheader("Tendencia Diaria")
            df_line = df.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
            fig_line = px.line(df_line, x='fecha_dia', y='revenue_amount', color='winning_channel', markers=True, template="plotly_dark")
            st.plotly_chart(fig_line, use_container_width=True)
        with c2:
            st.subheader("Share por Canal")
            st.plotly_chart(px.pie(df, values='revenue_amount', names='winning_channel', hole=0.5, template="plotly_dark"), use_container_width=True)

    with tab2:
        st.subheader("¿Qué días de la semana vendemos más?")
        # Ordenamos los días para que el gráfico tenga sentido
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_week = df.groupby('dia_semana')['revenue_amount'].sum().reindex(orden_dias).reset_index()
        
        fig_week = px.bar(df_week, x='dia_semana', y='revenue_amount', 
                          color='revenue_amount', color_continuous_scale='Blues',
                          template="plotly_dark", title="Revenue Total por Día de la Semana")
        st.plotly_chart(fig_week, use_container_width=True)
        st.info("💡 Este gráfico te dice qué días son los más rentables para tu negocio, ideal para planificar promociones.")

    with tab3:
        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.subheader("Análisis de Pareto (80/20)")
            df_p = df.groupby('winning_channel')['revenue_amount'].sum().sort_values(ascending=False).reset_index()
            df_p['acum'] = (df_p['revenue_amount'].cumsum() / df_p['revenue_amount'].sum()) * 100
            fig_p = go.Figure()
            fig_p.add_trace(go.Bar(x=df_p['winning_channel'], y=df_p['revenue_amount'], name="Revenue"))
            fig_p.add_trace(go.Scatter(x=df_p['winning_channel'], y=df_p['acum'], name="%", yaxis="y2", line=dict(color="#00ffcc")))
            fig_p.update_layout(template="plotly_dark", yaxis2=dict(overlaying='y', side='right', range=[0, 110]))
            st.plotly_chart(fig_p, use_container_width=True)
        
        with col_p2:
            st.subheader("Matriz de Eficiencia")
            df_eff = df.groupby('winning_channel').agg({'revenue_amount':['sum', 'mean'], 'winning_channel':'count'}).reset_index()
            df_eff.columns = ['canal', 'total', 'avg', 'count']
            st.plotly_chart(px.scatter(df_eff, x='count', y='avg', size='total', color='canal', template="plotly_dark"), use_container_width=True)

    with st.expander("🔍 Auditoría de Datos"):
        st.dataframe(df, use_container_width=True)