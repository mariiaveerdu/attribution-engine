import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# 1. CONFIGURACIÓN DE AGENCIA PRO
st.set_page_config(page_title="Marketing Executive Shell", layout="wide", page_icon="📈")

# Estilo CSS para que las métricas y contenedores se vean premium
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="metric-container"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 10px;
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
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return None

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=50)
    st.header("Control Panel")
    token = st.secrets.get("MOTHERDUCK_TOKEN") or st.text_input("Access Token", type="password")
    st.markdown("---")
    
if not token:
    st.info("Please enter your MotherDuck Token to initialize the engine.")
    st.stop()

df_raw = get_data(token)

if df_raw is not None:
    # Filtros avanzados en Sidebar
    canales = st.sidebar.multiselect("Canales de Adquisición", options=sorted(df_raw['winning_channel'].unique()), default=df_raw['winning_channel'].unique())
    df = df_raw[df_raw['winning_channel'].isin(canales)]

    # --- HEADER ---
    st.title("📊 Marketing Attribution Command Center")
    st.markdown(f"**Periodo analizado:** {df['fecha_dia'].min()} a {df['fecha_dia'].max()}")
    
    # --- FILA 1: KPIs MÉTRICAS DE IMPACTO ---
    m1, m2, m3, m4 = st.columns(4)
    total_rev = df['revenue_amount'].sum()
    total_conv = len(df)
    aov = total_rev / total_conv if total_conv > 0 else 0
    
    m1.metric("Revenue Total", f"{total_rev:,.0f}€")
    m2.metric("Conversiones", f"{total_conv:,}")
    m3.metric("AOV (Average Order Value)", f"{aov:,.2f}€")
    m4.metric("Canales Activos", f"{df['winning_channel'].nunique()}")

    st.markdown("### 🔦 Análisis de Performance")

    # --- FILA 2: EL CORAZÓN DEL DASHBOARD (Tendencia vs Mix) ---
    col_main, col_side = st.columns([7, 3])

    with col_main:
        # Gráfico de Líneas evolucionado: Muestra la tendencia acumulada o diaria
        df_daily = df.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
        fig_line = px.line(df_daily, x='fecha_dia', y='revenue_amount', color='winning_channel',
                           title="Evolución de Ingresos por Canal", markers=True,
                           template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Bold)
        fig_line.update_layout(hovermode="x unified", plot_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig_line, use_container_width=True)

    with col_side:
        # Gráfico de Donut: Para ver la cuota de mercado actual
        fig_donut = px.pie(df, values='revenue_amount', names='winning_channel', hole=.6,
                           title="Share of Wallet (Revenue %)", template="plotly_dark")
        fig_donut.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_donut, use_container_width=True)

    # --- FILA 3: PROFUNDIDAD ESTRATÉGICA (Scatter Plot de Eficiencia) ---
    st.markdown("### 🎯 Eficiencia de Canales")
    col_a, col_b = st.columns(2)

    with col_a:
        # Treemap: Para entender el volumen vs valor
        st.subheader("Jerarquía de Volumen de Ventas")
        fig_tree = px.treemap(df, path=['winning_channel'], values='revenue_amount',
                              color='revenue_amount', color_continuous_scale='RdBu_r', template="plotly_dark")
        st.plotly_chart(fig_tree, use_container_width=True)

    with col_b:
        # Scatter Plot: Relación entre número de ventas y dinero generado (Eficiencia)
        st.subheader("Matriz: Volumen vs Valor Medio")
        df_eff = df.groupby('winning_channel').agg({'revenue_amount':['sum', 'mean'], 'order_id':'count'}).reset_index()
        df_eff.columns = ['canal', 'total_revenue', 'avg_revenue', 'num_ventas']
        
        fig_scatter = px.scatter(df_eff, x='num_ventas', y='avg_revenue', size='total_revenue', color='canal',
                                 hover_name='canal', title="¿Qué canales traen tickets más caros?",
                                 template="plotly_dark", size_max=40)
        st.plotly_chart(fig_scatter, use_container_width=True)

    # --- FILA 4: DATA EXPLORER ---
    with st.expander("📂 Explorador de Registros (Auditoría de Atribución)"):
        st.write("Datos en crudo procesados por el modelo de atribución:")
        st.dataframe(df.sort_values(by='converted_at', ascending=False), use_container_width=True)

else:
    st.warning("⚠️ Sin datos. Asegúrate de que el proceso de dbt terminó correctamente en MotherDuck.")