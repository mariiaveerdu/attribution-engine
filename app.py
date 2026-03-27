import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. Configuración de la Página
st.set_page_config(
    page_title="Marketing Intelligence | Pro",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Custom para diseño "Cyberpunk/Professional"
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 28px; color: #00ffcc; }
    .main { background-color: #0e1117; }
    div.stButton > button:first-child {
        background-color: #00ffcc; color: black; border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Gestión del Token y Conexión
token = st.secrets.get("MOTHERDUCK_TOKEN") or st.sidebar.text_input("🔑 Token:", type="password")

@st.cache_data(ttl=600)
def get_advanced_data(md_token):
    con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
    df = con.sql("SELECT * FROM fct_attribute_last_click").df()
    con.close()
    return df

# --- INTERFAZ ---
st.title("💎 Marketing Attribution Intelligence")
st.caption("Analizando datos en tiempo real desde MotherDuck Cloud")

if token:
    try:
        df = get_data(token)
        
        # --- SIDEBAR FILTERS ---
        st.sidebar.header("🎯 Filtros")
        canales = st.sidebar.multiselect("Seleccionar Canales", 
                                        options=df['winning_channel'].unique(),
                                        default=df['winning_channel'].unique())
        
        df_filtered = df[df['winning_channel'].isin(canales)]

        # --- FILA 1: KPIs ---
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Revenue Total", f"{df_filtered['revenue_amount'].sum():,.0f}€", "Sales")
        m2.metric("Conversiones", f"{len(df_filtered)}", "Orders")
        m3.metric("AOV", f"{df_filtered['revenue_amount'].mean():,.2f}€", "Ticket Medio")
        m4.metric("Top Canal", df_filtered.groupby('winning_channel')['revenue_amount'].sum().idxmax())

        st.markdown("---")

        # --- FILA 2: GRÁFICOS ---
        c1, c2 = st.columns([6, 4])

        with c1:
            st.subheader("📈 Rendimiento Histórico por Canal")
            # Agrupamos por canal para el gráfico de barras
            chart_data = df_filtered.groupby('winning_channel')['revenue_amount'].sum().sort_values(ascending=False).reset_index()
            fig_bar = px.bar(chart_data, x='winning_channel', y='revenue_amount',
                            color='revenue_amount', color_continuous_scale='Viridis',
                            text_auto='.2s', template="plotly_dark")
            fig_bar.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)

        with c2:
            st.subheader("🥧 Cuota de Mercado")
            fig_pie = px.pie(df_filtered, values='revenue_amount', names='winning_channel', 
                             hole=0.6, template="plotly_dark",
                             color_discrete_sequence=px.colors.sequential.Cyan_r)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- FILA 3: EL FUNNEL ---
        st.markdown("---")
        st.subheader("🌪️ Proporción de Ingresos por Canal")
        fig_funnel = px.funnel(chart_data, x='revenue_amount', y='winning_channel',
                               color_discrete_sequence=['#00ffcc'], template="plotly_dark")
        st.plotly_chart(fig_funnel, use_container_width=True)

        # --- TABLA DE DATOS ---
        with st.expander("🔍 Ver transacciones detalladas"):
            st.dataframe(df_filtered.style.background_gradient(cmap='Blues', subset=['revenue_amount']), 
                         use_container_width=True)

    except Exception as e:
        st.error(f"Error: {e}")
else:
    st.warning("Introduce tu token en el menú lateral para desbloquear el Dashboard.")