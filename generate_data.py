import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# Ruta hacia la carpeta seeds de dbt (Asegúrate de que esta ruta existe)
folder = 'dbt_project/seeds'

def generate_data():
    print("Configurando datos sucios...")
    
    # 1. TRÁFICO WEB (Sesiones)
    canales = ['Paid Search', 'social_media', 'ORGANIC', 'Direct', 'Email', None]
    
    sesiones = []
    for i in range(1000):
        u_id = f"U{np.random.randint(1, 100)}"
        dt = datetime(2026, 1, 1) + timedelta(days=np.random.randint(0, 30), minutes=np.random.randint(0, 1440))
        
        # Un 10% de las fechas irán en formato raro para obligarnos a limpiar
        ts = dt.strftime('%d/%m/%Y %H:%M') if np.random.random() < 0.1 else dt.isoformat()
        
        sesiones.append({
            'session_id': f"sess_{i}",
            'user_id': u_id,
            'session_at': ts,
            'utm_source': np.random.choice(canales)
        })

    df_sesiones = pd.DataFrame(sesiones)
    # Añadimos 20 duplicados exactos para practicar el DISTINCT
    df_sesiones = pd.concat([df_sesiones, df_sesiones.sample(20)])
    df_sesiones.to_csv(f'{folder}/raw_web_traffic.csv', index=False)

    # 2. CONVERSIONES (Ventas)
    ventas = []
    for i in range(150):
        u_id = f"U{np.random.randint(1, 120)}" 
        dt_v = datetime(2026, 2, 1) + timedelta(days=np.random.randint(0, 5))
        
        # CORRECCIÓN AQUÍ: Usamos round() de Python, no el método de numpy
        rev_value = round(np.random.uniform(50, 200), 2)
        
        ventas.append({
            'order_id': f"ORD{1000+i}",
            'user_id': u_id,
            'converted_at': dt_v.isoformat(),
            'revenue': str(rev_value) # Lo pasamos a string a propósito
        })

    df_ventas = pd.DataFrame(ventas)
    df_ventas.to_csv(f'{folder}/raw_conversions.csv', index=False)
    print(f"✅ Archivos guardados con éxito en {folder}")

if __name__ == "__main__":
    generate_data()