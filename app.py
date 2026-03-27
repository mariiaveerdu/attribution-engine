import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# 1. Configuración básica
st.set_page_config(page_title="Marketing Attribution", layout="wide")

# 2. Gestión del Token (Prioriza Streamlit Cloud Secrets)
if "MOTHERDUCK_TOKEN" in st.secrets:
    token = st.secrets["MOTHERDUCK_TOKEN"]
else:
    st.sidebar.warning("⚠️ No se encontró el token en Secrets.")
    token = st.sidebar.text_input("Introduce tu Token manualmente:", type="password")

# 3. Función para traer los datos
@st.cache_data(ttl=600)
def get_data(md_token):
    # Conexión a MotherDuck
    con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
    
    # Query a tu modelo de dbt
    df = con.sql("SELECT * FROM fct_attribute_last_click").df()
    con.close()
    return df

# 4. Interfaz Visual
st.title("🎯 Attribution Dashboard")
st.markdown("Análisis de conversiones por canal (Modelo: **Last Click**)")

if token:
    try:
        df = get_data(token)

        # --- KPIs ---
        total_rev = df['revenue_amount'].sum()
        col1, col2 = st.columns(2)
        col1.metric("Revenue Total", f"{total_rev:,.2f} €")
        col2.metric("Total Órdenes", len(df))

        # --- GRÁFICO ---
        st.subheader("Ventas por Canal")
        fig = px.bar(
            df.groupby('winning_channel')['revenue_amount'].sum().reset_index(),
            x='winning_channel', 
            y='revenue_amount',
            color='winning_channel',
            template="plotly_dark"
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- TABLA ---
        st.subheader("Detalle de Datos")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
else:
    st.info("💡 Por favor, configura el token para ver las gráficas.")