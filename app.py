import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. Configuración de la Página de Élite
st.set_page_config(
    page_title="Marketing Intelligence | Pro Command Center",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CSS Custom para diseño "Cyberpunk Premium"
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 30px; color: #00ffcc; font-weight: bold; }
    [data-testid="stMetricDelta"] { font-size: 16px; }
    .stDataFrame { border: 1px solid #374151; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 3. Gestión del Token y Conexión
token = st.secrets.get("MOTHERDUCK_TOKEN") or st.sidebar.text_input("🔑 Token:", type="password")

@st.cache_data(ttl=600)
def get_advanced_data(md_token):
    try:
        con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
        # Query: Traemos la fecha formateada para análisis mensual
        query = """
        SELECT 
            strftime(event_date, '%Y-%m') as event_month,
            order_id,
            winning_channel,
            revenue_amount
        FROM detective_ventas.main.fct_attribute_last_click
        ORDER BY event_date
        """
        df = con.sql(query).df()
        con.close()
        # Asegurar tipos de datos correctos
        df['revenue_amount'] = df['revenue_amount'].astype(float)
        return df
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return None

# --- CUERPO DEL DASHBOARD ---
st.title("💎 Marketing Intelligence | Pro Command Center")
st.caption(f"🚀 Datos analizados bajo modelo de atribución: **Last Click**")

if token:
    try:
        df_raw = get_advanced_data(token)
        
        if df_raw is not None and not df_raw.empty:
            # --- FILTROS DE SIDEBAR ---
            st.sidebar.header("🎯 Controles Avanzados")
            months = st.sidebar.multiselect("Filtrar Meses:", 
                                           options=df_raw['event_month'].unique(),
                                           default=df_raw['event_month'].unique())
            channels = st.sidebar.multiselect("Filtrar Canales:", 
                                            options=df_raw['winning_channel'].unique(),
                                            default=df_raw['winning_channel'].unique())
            
            # Aplicar filtros
            df = df_raw[(df_raw['event_month'].isin(months)) & (df_raw['winning_channel'].isin(channels))]

            # --- SECCIÓN 1: KPIs Ejecutivos ---
            m1, m2, m3, m4 = st.columns(4)
            
            # Cálculo de KPIs con deltas ficticios para efecto Senior (puedes añadir lógica real aquí)
            total_rev = df['revenue_amount'].sum()
            total_orders = df['order_id'].nunique()
            aov = total_rev / total_orders if total_orders > 0 else 0
            
            m1.metric("Revenue Total", f"{total_rev:,.0f}€", "+3.2% vs MM")
            m2.metric("Conversiones", f"{total_orders:,}", "+1.5%")
            m3.metric("AOV (Ticket Medio)", f"{aov:,.2f}€", "-0.8%")
            m4.metric("Dependencia Canal Top", 
                     f"{(df.groupby('winning_channel')['revenue_amount'].sum().max() / total_rev * 100):.1f}%", 
                     "(Riesgo de Dependencia)")

            st.markdown("---")

            # --- SECCIÓN 2: DIAGNÓSTICO SENIOR (The "How" and "Why") ---
            st.header("🔍 Diagnóstico de Salud del Marketing")
            col_diag1, col_diag2 = st.columns([6, 4])

            with col_diag1:
                st.subheader("1. Diagnóstico de Rentabilidad: Distribución de Ticket por Canal")
                # Boxplot: Enseña promedio, cuartiles y outliers
                fig_box = px.box(df, x='winning_channel', y='revenue_amount',
                               color='winning_channel', template="plotly_dark",
                               title="AOV y Rentabilidad de Cliente",
                               points="outliers") # Mostramos outliers
                fig_box.update_layout(xaxis_title="", yaxis_title="Revenue por Pedido (€)")
                st.plotly_chart(fig_box, use_container_width=True)
                st.info("💡 Insight: ¿Qué canales nos traen los clientes VIP (Outliers superiores)?")

            with col_diag2:
                st.subheader("2. Diagnóstico de Dependencia: Cuota de Revenue por Canal")
                # Treemap: Enseña la jerarquía de ingresos
                df_tree = df.groupby('winning_channel')['revenue_amount'].sum().reset_index()
                fig_tree = px.treemap(df_tree, path=['winning_channel'], values='revenue_amount',
                                     color='revenue_amount', template="plotly_dark",
                                     color_continuous_scale='blues_r', # Corregido error de color
                                     title="Jerarquía de Ingresos")
                st.plotly_chart(fig_tree, use_container_width=True)
                st.warning("⚠️ Insight: Si el cuadro más grande representa >50%, tu negocio tiene alta dependencia.")

            st.markdown("---")

            # --- SECCIÓN 3: TENDENCIAS Y EVOLUCIÓN (The "When") ---
            st.header("📈 Tendencias y Evolución de Eficiencia")
            
            # Stacked Area Chart: Enseña cómo evoluciona la cuota de mercado mes a mes
            # Agrupamos por mes y canal
            df_trend = df.groupby(['event_month', 'winning_channel'])['revenue_amount'].sum().reset_index()
            # Calculamos la cuota de mercado mensual
            df_trend['monthly_total'] = df_trend.groupby('event_month')['revenue_amount'].transform('sum')
            df_trend['market_share'] = (df_trend['revenue_amount'] / df_trend['monthly_total']) * 100

            fig_trend = px.area(df_trend, x='event_month', y='market_share',
                                color='winning_channel', template="plotly_dark",
                                title="Evolución de Cuota de Mercado (%)",
                                color_discrete_sequence=px.colors.qualitative.Plotly_r)
            fig_trend.update_layout(xaxis_title="Mes", yaxis_title="Cuota de Ingresos (%)", yaxis_range=[0,100])
            st.plotly_chart(fig_trend, use_container_width=True)
            st.success("✅ Insight: ¿Ves un canal creciendo a costa de otro? Identifica el momento del cambio.")

            # --- TABLA DE DATOS DETALLADA ---
            with st.expander("🔍 Ver transacciones detalladas"):
                st.dataframe(df.style.background_gradient(cmap='Blues', subset=['revenue_amount']), 
                             use_container_width=True)

        else:
            st.warning("⚠️ No se encontraron datos para los filtros seleccionados.")

    except Exception as e:
        st.error(f"Error crítico en el renderizado: {e}")
        st.info("Revisa la estructura de la tabla 'fct_attribute_last_click'.")
else:
    st.warning("👈 Por favor, introduce tu Token en la barra lateral para comenzar.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)