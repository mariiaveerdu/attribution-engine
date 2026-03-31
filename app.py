import streamlit as st
import duckdb
import pandas as pd
import plotly.express as px

# 1. Configuración de la Página
st.set_page_config(page_title="Marketing Intelligence Pro", layout="wide")

# 2. Conexión y Carga de Datos (Limpieza Senior)
@st.cache_data(ttl=600)
def get_data(md_token):
    try:
        con = duckdb.connect(f'md:detective_ventas?motherduck_token={md_token}')
        # Traemos los datos y normalizamos columnas a minúsculas
        df = con.sql("SELECT * FROM detective_ventas.main.fct_attribute_last_click").df()
        con.close()
        df.columns = [c.lower() for c in df.columns]
        
        # Gestión de fechas y meses
        if 'converted_at' in df.columns:
            df['converted_at'] = pd.to_datetime(df['converted_at'])
            df['event_month'] = df['converted_at'].dt.strftime('%Y-%m')
        
        # Limpieza de Revenue
        df['revenue_amount'] = pd.to_numeric(df['revenue_amount'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return None

# --- ESTRUCTURA DEL DASHBOARD ---
st.title("💎 Marketing Intelligence | Pro Command Center")

# Sidebar para el Token
token = st.secrets.get("MOTHERDUCK_TOKEN") or st.sidebar.text_input("🔑 Token:", type="password")

if token:
    df = get_data(token)
    
    if df is not None and not df.empty:
        # --- FILTROS ---
        st.sidebar.header("🎯 Filtros")
        canales = st.sidebar.multiselect("Canales:", options=df['winning_channel'].unique(), default=df['winning_channel'].unique())
        df_filtered = df[df['winning_channel'].isin(canales)]

        # --- KPIs ---
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue Total", f"{df_filtered['revenue_amount'].sum():,.0f}€")
        c2.metric("Total Pedidos", len(df_filtered))
        c3.metric("AOV", f"{df_filtered['revenue_amount'].mean():,.2f}€")

        st.markdown("---")

        # --- GRÁFICOS SENIOR ---
        col_a, col_b = st.columns(2)

        with col_a:
            st.subheader("📊 Distribución de Ingresos (Boxplot)")
            fig_box = px.box(df_filtered, x='winning_channel', y='revenue_amount', color='winning_channel', template="plotly_dark")
            st.plotly_chart(fig_box, use_container_width=True)

        with col_b:
            st.subheader("🥧 Cuota de Mercado (Treemap)")
            fig_tree = px.treemap(df_filtered, path=['winning_channel'], values='revenue_amount', color='revenue_amount', template="plotly_dark")
            st.plotly_chart(fig_tree, use_container_width=True)

        # --- GRÁFICA 4: EVOLUCIÓN ---
st.header("📈 Evolución Diaria de Ingresos")

if 'converted_at' in df_filtered.columns:
    # 1. Creamos una copia para no romper el dataframe original
    df_ts = df_filtered.copy()
    
    # 2. Redondeamos la fecha al DÍA (quitamos horas/minutos/segundos)
    df_ts['fecha_dia'] = df_ts['converted_at'].dt.date
    
    # 3. Agrupamos por Día y Canal
    df_trend = df_ts.groupby(['fecha_dia', 'winning_channel'])['revenue_amount'].sum().reset_index()
    
    # 4. Ordenamos por fecha para que la línea no salte de un lado a otro
    df_trend = df_trend.sort_values('fecha_dia')

    # 5. Dibujamos el gráfico (usamos marcadores para que se vean los puntos aunque haya pocos días)
    fig_trend = px.area(
        df_trend, 
        x='fecha_dia', 
        y='revenue_amount', 
        color='winning_channel',
        line_group='winning_channel',
        markers=True, # IMPORTANTE: Así verás los puntos exactos del 31 y el 1
        template="plotly_dark",
        title="Revenue Diario por Canal de Atribución"
    )
    
    # Ajustamos el eje X para que no invente horas
    fig_trend.update_xaxes(type='category', tickangle=45) 
    
    st.plotly_chart(fig_trend, use_container_width=True)
else:
    st.warning("No se puede generar la evolución porque falta la columna de fecha.")

        # --- TABLA DETALLADA ---
        with st.expander("🔍 Ver transacciones detalladas"):
            # Quitamos el gradient para evitar el error de matplotlib por ahora y asegurar que cargue
            st.dataframe(df_filtered, use_container_width=True)
    else:
        st.warning("No se encontraron datos. Revisa tu tabla en MotherDuck.")
else:
    st.info("👈 Introduce tu Token en el menú lateral.")