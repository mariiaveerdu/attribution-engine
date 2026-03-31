import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# 1. Configuración de la Página de Élite
st.set_page_config(
    page_title="Marketing Intelligence Pro",
    page_icon="💎",
    layout="wide"
)

# 2. Función de Carga de Datos (Limpieza y Normalización Senior)
@st.cache_data(ttl=600)
def get_data(md_token):
    try:
        # Conexión a MotherDuck
        con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
        
        # Traemos los datos de la tabla
        df = con.sql("SELECT * FROM detective_ventas.main.fct_attribute_last_click").df()
        con.close()
        
        # Normalizamos nombres de columnas a minúsculas
        df.columns = [c.lower() for c in df.columns]
        
        # Gestión de fechas
        if 'converted_at' in df.columns:
            df['converted_at'] = pd.to_datetime(df['converted_at'])
            # Creamos la columna de fecha sin hora para agrupar
            df['fecha_dia'] = df['converted_at'].dt.date
        
        # Aseguramos que el revenue sea numérico
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error de conexión o de tabla: {e}")
        return None

# --- ESTRUCTURA DE LA INTERFAZ ---

st.title("💎 Marketing Intelligence | Command Center")
st.caption("Análisis de Atribución Last Click - Visualización de Tendencias en Tiempo Real")

# Sidebar para el Token
token = st.secrets.get("MOTHERDUCK_TOKEN") or st.sidebar.text_input("🔑 Token de MotherDuck:", type="password")

if token:
    df_raw = get_data(token)
    
    if df_raw is not None and not df_raw.empty:
        # --- FILTROS ---
        st.sidebar.header("🎯 Filtros de Campaña")
        canales_disponibles = sorted(df_raw['winning_channel'].unique())
        canales_sel = st.sidebar.multiselect("Seleccionar Canales:", options=canales_disponibles, default=canales_disponibles)
        
        df = df_raw[df_raw['winning_channel'].isin(canales_sel)]

        # --- SECCIÓN 1: KPIs ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Revenue Total", f"{df['revenue_amount'].sum():,.2f} €")
        m2.metric("Conversiones", f"{len(df):,}")
        m3.metric("Ticket Medio (AOV)", f"{df['revenue_amount'].mean():,.2f} €")

        st.markdown("---")

        # --- SECCIÓN 2: DIAGNÓSTICOS VISUALES ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📊 Distribución de Tickets")
            fig_box = px.box(df, x='winning_channel', y='revenue_amount', 
                             color='winning_channel', template="plotly_dark")
            fig_box.update_layout(xaxis_title="", yaxis_title="Euros (€)")
            st.plotly_chart(fig_box, use_container_width=True)

        with col_right:
            st.subheader("🥧 Cuota de Mercado")
            fig_tree = px.treemap(df, path=['winning_channel'], values='revenue_amount', 
                                  color='revenue_amount', template="plotly_dark",
                                  color_continuous_scale='Blues')
            st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown("---")

        # --- SECCIÓN 3: EVOLUCIÓN TEMPORAL (VERSIÓN LÍNEAS) ---
        st.header("📈 Tendencia Diaria de Ingresos")
        
        # Agrupamos por día y canal
        df_trend = df.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
        df_trend = df_trend.sort_values('fecha_dia')

        # Gráfico de Líneas Pro
        fig_line = px.line(
            df_trend, 
            x='fecha_dia', 
            y='revenue_amount', 
            color='winning_channel',
            markers=True, 
            template="plotly_dark",
            title="Evolución de Ventas por Canal"
        )
        
        # Estilo Senior para las líneas
        fig_line.update_traces(line=dict(width=3), marker=dict(size=10))
        # Forzamos el eje X para que sea categórico y no deje huecos
        fig_line.update_xaxes(type='category', title="Fecha de Conversión")
        fig_line.update_yaxes(title="Ingresos (€)", gridcolor='#374151')

        st.plotly_chart(fig_line, use_container_width=True)

        # --- SECCIÓN 4: EXPLORADOR DE DATOS ---
        with st.expander("🔍 Ver transacciones detalladas"):
            st.dataframe(df, use_container_width=True)
            
    else:
        st.warning("⚠️ No hay datos disponibles para mostrar.")

else:
    st.info("👈 Introduce tu Token en la barra lateral para activar el dashboard.")