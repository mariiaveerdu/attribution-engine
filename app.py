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

# 2. Función de Carga de Datos (Limpieza y Normalización)
@st.cache_data(ttl=600)
def get_data(md_token):
    try:
        # Conexión a MotherDuck
        con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
        
        # Traemos los datos de tu tabla de dbt
        df = con.sql("SELECT * FROM detective_ventas.main.fct_attribute_last_click").df()
        con.close()
        
        # Normalizamos nombres de columnas a minúsculas para evitar errores
        df.columns = [c.lower() for c in df.columns]
        
        # Convertimos la fecha correctamente
        if 'converted_at' in df.columns:
            df['converted_at'] = pd.to_datetime(df['converted_at'])
            # Creamos una columna solo con la fecha (sin horas) para los gráficos diarios
            df['fecha_dia'] = df['converted_at'].dt.date
        
        # Aseguramos que el revenue sea un número
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error de conexión o de tabla: {e}")
        return None

# --- ESTRUCTURA DE LA INTERFAZ ---

st.title("💎 Marketing Intelligence | Command Center")
st.caption("Análisis de Atribución Last Click - Datos en tiempo real desde MotherDuck")

# Sidebar para el Token (Prioriza st.secrets de Streamlit Cloud)
token = st.secrets.get("MOTHERDUCK_TOKEN") or st.sidebar.text_input("🔑 Introduce tu Token:", type="password")

if token:
    df_raw = get_data(token)
    
    if df_raw is not None and not df_raw.empty:
        # --- FILTROS EN SIDEBAR ---
        st.sidebar.header("🎯 Controles")
        canales_disponibles = sorted(df_raw['winning_channel'].unique())
        canales_sel = st.sidebar.multiselect("Filtrar Canales:", options=canales_disponibles, default=canales_disponibles)
        
        # Aplicamos el filtro
        df = df_raw[df_raw['winning_channel'].isin(canales_sel)]

        # --- SECCIÓN 1: KPIs ---
        m1, m2, m3 = st.columns(3)
        m1.metric("Revenue Total", f"{df['revenue_amount'].sum():,.2f} €")
        m2.metric("Conversiones", f"{len(df):,}")
        m3.metric("Ticket Medio (AOV)", f"{df['revenue_amount'].mean():,.2f} €")

        st.markdown("---")

        # --- SECCIÓN 2: DIAGNÓSTICO DE RENTABILIDAD ---
        col_left, col_right = st.columns(2)

        with col_left:
            st.subheader("📊 Distribución de Tickets por Canal")
            # El Boxplot es clave para ver dónde están los clientes que más gastan
            fig_box = px.box(df, x='winning_channel', y='revenue_amount', 
                             color='winning_channel', template="plotly_dark")
            st.plotly_chart(fig_box, use_container_width=True)

        with col_right:
            st.subheader("🥧 Cuota de Mercado (Revenue)")
            # El Treemap ayuda a ver visualmente qué canal domina el presupuesto
            fig_tree = px.treemap(df, path=['winning_channel'], values='revenue_amount', 
                                  color='revenue_amount', template="plotly_dark",
                                  color_continuous_scale='Blues')
            st.plotly_chart(fig_tree, use_container_width=True)

        st.markdown("---")

        # --- SECCIÓN 3: EVOLUCIÓN TEMPORAL ---
        st.header("📈 Evolución Diaria de Ingresos")
        
        # Agrupamos por día y canal para ver la tendencia
        df_trend = df.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
        df_trend = df_trend.sort_values('fecha_dia')

        # Usamos gráfico de BARRAS porque con solo 2 días (31 Ene y 1 Feb) se entiende mucho mejor
        fig_trend = px.bar(
            df_trend, 
            x='fecha_dia', 
            y='revenue_amount', 
            color='winning_channel',
            barmode='group',
            template="plotly_dark",
            labels={'fecha_dia': 'Día de la Conversión', 'revenue_amount': 'Ingresos (€)'}
        )
        # Forzamos el eje X para que no invente horas, solo muestre los días con datos
        fig_trend.update_xaxes(type='category')
        st.plotly_chart(fig_trend, use_container_width=True)

        # --- SECCIÓN 4: EXPLORADOR DE DATOS ---
        with st.expander("🔍 Ver transacciones detalladas (Raw Data)"):
            st.dataframe(df, use_container_width=True)
            
    else:
        st.warning("⚠️ No se han podido cargar datos. Verifica que la tabla 'fct_attribute_last_click' existe en MotherDuck.")

else:
    st.info("👈 Por favor, introduce tu Token de MotherDuck en la barra lateral para activar el dashboard.")
    st.image("https://streamlit.io/images/brand/streamlit-mark-color.png", width=100)