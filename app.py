import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. CONFIGURACIÓN ESTÉTICA PRO
st.set_page_config(page_title="Marketing OS | Enterprise Edition", layout="wide", page_icon="🚀")

st.markdown("""
    <style>
    .main { background-color: #0b0e14; }
    div[data-testid="stMetric"] {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 12px;
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
        # Extraer dimensiones temporales para el Heatmap
        df['hora'] = df['converted_at'].dt.hour
        df['dia_semana'] = df['converted_at'].dt.day_name()
        df['fecha_dia'] = df['converted_at'].dt.date
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error en datos: {e}")
        return None

# --- SIDEBAR & AUTH ---
with st.sidebar:
    st.title("🛡️ Admin Panel")
    token = st.secrets.get("MOTHERDUCK_TOKEN") or st.text_input("Token de Acceso", type="password")
    if not token:
        st.warning("Introduce el Token para continuar.")
        st.stop()
    st.markdown("---")
    st.caption("v2.5 Enterprise Edition")

df_raw = get_data(token)

if df_raw is not None:
    # --- PROCESAMIENTO DE FILTROS ---
    canales_all = sorted(df_raw['winning_channel'].unique())
    sel_canales = st.sidebar.multiselect("Filtrar Canales", canales_all, default=canales_all)
    df = df_raw[df_raw['winning_channel'].isin(sel_canales)]

    # --- HEADER & KPIs CON DELTAS (Simulados para el ejemplo) ---
    st.title("📈 Marketing Intelligence OS")
    
    k1, k2, k3, k4 = st.columns(4)
    rev_total = df['revenue_amount'].sum()
    conv_total = len(df)
    aov = rev_total / conv_total if conv_total > 0 else 0
    
    k1.metric("Revenue Total", f"{rev_total:,.0f}€", "+12% vs MP")
    k2.metric("Conversiones", f"{conv_total:,}", "+5% vs MP")
    k3.metric("Ticket Medio (AOV)", f"{aov:,.2f}€", "-2%")
    k4.metric("ROI Estimado", "4.2x", "+0.3")

    # --- NAVEGACIÓN POR PESTAÑAS (TABS) ---
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Performance", "🕒 Timing & Heatmap", "🎯 Pareto & Eficiencia", "📑 Auditoría"])

    # --- TAB 1: PERFORMANCE GENERAL ---
    with tab1:
        c1, c2 = st.columns([7, 3])
        with c1:
            st.subheader("Tendencia de Ingresos Diaria")
            df_line = df.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
            fig_line = px.line(df_line, x='fecha_dia', y='revenue_amount', color='winning_channel', markers=True, template="plotly_dark")
            st.plotly_chart(fig_line, use_container_width=True)
        with c2:
            st.subheader("Share por Canal")
            fig_pie = px.pie(df, values='revenue_amount', names='winning_channel', hole=0.5, template="plotly_dark")
            st.plotly_chart(fig_pie, use_container_width=True)

    # --- TAB 2: TIMING & HEATMAP (CUÁNDO OCURRE) ---
    with tab2:
        st.subheader("Mapa de Calor: Concentración de Ventas (Hora vs Día)")
        # Crear matriz para heatmap
        orden_dias = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        df_heat = df.groupby(['dia_semana', 'hora'])['revenue_amount'].sum().reset_index()
        df_pivot = df_heat.pivot(index='dia_semana', columns='hora', values='revenue_amount').reindex(orden_dias)
        
        fig_heat = px.imshow(df_pivot, labels=dict(x="Hora del Día", y="Día de la Semana", color="Revenue"),
                            x=list(range(24)), template="plotly_dark", color_continuous_scale='Viridis')
        st.plotly_chart(fig_heat, use_container_width=True)
        st.info("💡 Consejo: Identifica las horas 'pico' para lanzar tus campañas de email o ajustar pujas en Ads.")

    # --- TAB 3: PARETO & EFICIENCIA (ESTRATEGIA SENIOR) ---
    with tab3:
        col_p1, col_p2 = st.columns(2)
        
        with col_p1:
            st.subheader("Análisis de Pareto (80/20)")
            df_pareto = df.groupby('winning_channel')['revenue_amount'].sum().sort_values(ascending=False).reset_index()
            df_pareto['perc'] = (df_pareto['revenue_amount'].cumsum() / df_pareto['revenue_amount'].sum()) * 100
            
            fig_pareto = go.Figure()
            fig_pareto.add_trace(go.Bar(x=df_pareto['winning_channel'], y=df_pareto['revenue_amount'], name="Revenue"))
            fig_pareto.add_trace(go.Scatter(x=df_pareto['winning_channel'], y=df_pareto['perc'], name="% Acumulado", yaxis="y2", line=dict(color="#00ffcc")))
            fig_pareto.update_layout(template="plotly_dark", yaxis2=dict(overlaying='y', side='right', range=[0, 110]), showlegend=False)
            st.plotly_chart(fig_pareto, use_container_width=True)

        with col_p2:
            st.subheader("Matriz de Eficiencia: Volumen vs Calidad")
            df_eff = df.groupby('winning_channel').agg({'revenue_amount':['sum', 'mean'], 'order_id':'count'}).reset_index()
            df_eff.columns = ['canal', 'total', 'avg', 'count']
            fig_scatter = px.scatter(df_eff, x='count', y='avg', size='total', color='canal', 
                                    template="plotly_dark", title="Burbuja = Revenue Total")
            st.plotly_chart(fig_scatter, use_container_width=True)

    # --- TAB 4: AUDITORÍA DE DATOS ---
    with tab4:
        st.subheader("Registros Detallados")
        st.dataframe(df.sort_values('converted_at', ascending=False), use_container_width=True)

else:
    st.error("Error al cargar la base de datos.")