"""
================================================================================
SISTEMA DE MONITOREO ACUEDUCTO - DASHBOARD PROFESIONAL
Versión: 2.0
Sensores: Temperatura, Humedad, Caudal, Cloro, Nivel, Altura, Presión
Plataformas: Wokwi → ThingSpeak → GitHub → Streamlit
================================================================================
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np
import time

# ============================================================================
# 1. CONFIGURACIÓN DE PÁGINA
# ============================================================================
st.set_page_config(
    page_title="Sistema Monitoreo Acueducto",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# 2. CREDENCIALES THINGSPEAK
# ============================================================================
try:
    API_KEY = st.secrets["THINGSPEAK_API_KEY"]
    CHANNEL_ID = st.secrets["THINGSPEAK_CHANNEL_ID"]
except:
    API_KEY = "XXXXXXXXXXXXXXXX"
    CHANNEL_ID = "1234567"

# ============================================================================
# 3. FUNCIONES AUXILIARES
# ============================================================================
@st.cache_data(ttl=30)
def obtener_datos(num_puntos=100):
    """Obtiene datos desde ThingSpeak"""
    url = f"https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json"
    params = {"api_key": API_KEY, "results": num_puntos}
    try:
        respuesta = requests.get(url, params=params, timeout=10)
        respuesta.raise_for_status()
        datos = respuesta.json()
        df = pd.DataFrame(datos["feeds"])
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.rename(columns={
            "field1": "Temperatura",
            "field2": "Humedad",
            "field3": "Caudal",
            "field4": "Cloro",
            "field5": "Nivel",
            "field6": "Altura",
            "field7": "Presion",
            "field8": "Estado"
        })
        for col in ["Temperatura", "Humedad", "Caudal", 
                    "Cloro", "Nivel", "Altura", "Presion"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df.dropna(subset=["Temperatura", "Humedad"])
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def crear_gauge(valor, minimo, maximo, titulo, unidad, zonas):
    """Crea gauge chart semicircular con zonas de color"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=valor,
        title={"text": titulo, "font": {"size": 18}},
        number={"suffix": unidad, "font": {"size": 40}},
        gauge={
            "axis": {"range": [minimo, maximo], "tickwidth": 1},
            "bar": {"color": "#1e3a8a", "thickness": 0.75},
            "steps": zonas,
            "threshold": {
                "line": {"color": "red", "width": 3},
                "thickness": 0.75,
                "value": maximo * 0.9
            }
        }
    ))
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=60, b=20))
    return fig


def verificar_alarmas(df):
    """Verifica alarmas según umbrales"""
    ultima = df.iloc[-1]
    alertas = []
    
    if ultima["Temperatura"] > 35:
        alertas.append({"tipo": "ALTA", "msg": f"Temperatura alta: {ultima['Temperatura']:.1f}°C"})
    if ultima["Cloro"] > 4:
        alertas.append({"tipo": "CRITICA", "msg": f"Cloro elevado: {ultima['Cloro']:.2f} ppm"})
    if ultima["Nivel"] < 20:
        alertas.append({"tipo": "MEDIA", "msg": f"Nivel bajo: {ultima['Nivel']:.1f}%"})
    if ultima["Presion"] > 8:
        alertas.append({"tipo": "ALTA", "msg": f"Presión alta: {ultima['Presion']:.2f} bar"})
    
    return alertas


# ============================================================================
# 4. SIDEBAR - NAVEGACIÓN
# ============================================================================
with st.sidebar:
    st.markdown("""
