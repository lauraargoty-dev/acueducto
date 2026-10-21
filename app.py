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
    

        
💧

        
Acueducto IoT

        
Monitoreo en tiempo real

    

    """, unsafe_allow_html=True)
    
    st.markdown("---")
    pagina = st.radio(
        "Navegación",
        [" Home", "📈 Gráficas Históricas", "🔔 Alarmas", 
         "🌡️ Temperatura y Humedad", "📥 Descargas"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.subheader("⚙️ Configuración")
    num_puntos = st.slider("Lecturas", 10, 500, 100, 10)
    auto_refresh = st.checkbox("⚡ Auto-refresh (30s)", value=False)
    
    if st.button("🔄 Actualizar", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================================================
# 5. CARGAR DATOS
# ============================================================================
df = obtener_datos(num_puntos)

if df is None or df.empty:
    st.error("❌ No se pudieron obtener datos. Verifica API Key y Channel ID.")
    st.stop()

# ============================================================================
# 6. PÁGINA: HOME
# ============================================================================
if pagina == " Home":
    st.markdown("""
    # 💧 Sistema de Monitoreo Acueducto
    Dashboard interactivo para visualizar datos en tiempo real del proyecto 
    de monitoreo del acueducto.
    """)
    
    # Última lectura
    ultima = df.iloc[-1]
    fecha = ultima["created_at"].strftime("%Y-%m-%d %H:%M:%S")
    st.caption(f"Última actualización: {fecha}")
    
    # Métricas en grid
    st.markdown("### 📊 Valores de los sensores en la última lectura")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Caudal (L/min)", f"{ultima['Caudal']:.2f}")
    with col2:
        st.metric("Cloro (ppm)", f"{ultima['Cloro']:.2f}")
    with col3:
        st.metric("Nivel (%)", f"{ultima['Nivel']:.2f}")
    with col4:
        st.metric("Altura (m)", f"{ultima['Altura']:.2f}")
    
    col5, col6, col7 = st.columns(3)
    with col5:
        st.metric("Temperatura (°C)", f"{ultima['Temperatura']:.2f}")
    with col6:
        st.metric("Humedad (%)", f"{ultima['Humedad']:.2f}")
    with col7:
        st.metric("Presión (bar)", f"{ultima['Presion']:.2f}")
    
    # Estado del sistema
    st.markdown("---")
    if ultima["Estado"] == "1":
        st.success("✅ Sistema operativo - Todos los sensores activos")
    else:
        st.error(" Sistema inactivo")

# ============================================================================
# 7. PÁGINA: GRÁFICAS HISTÓRICAS
# ============================================================================
elif pagina == "📈 Gráficas Históricas":
    st.markdown("# 📈 Gráficas Históricas")
    st.markdown("Visualización de tendencias de todos los sensores.")
    
    # Gráfica multi-eje
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            "Temperatura (°C)", "Humedad (%)",
            "Caudal (L/min)", "Cloro (ppm)",
            "Nivel (%)", "Presión (bar)"
        ),
        vertical_spacing=0.12
    )
    
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Temperatura"],
                            name="Temp", line=dict(color="#ef4444", width=2)),
                  row=1, col=1)
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Humedad"],
                            name="Hum", line=dict(color="#3b82f6", width=2)),
                  row=1, col=2)
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Caudal"],
                            name="Caudal", line=dict(color="#10b981", width=2)),
                  row=2, col=1)
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Cloro"],
                            name="Cloro", line=dict(color="#f59e0b", width=2)),
                  row=2, col=2)
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Nivel"],
                            name="Nivel", line=dict(color="#8b5cf6", width=2)),
                  row=3, col=1)
    fig.add_trace(go.Scatter(x=df["created_at"], y=df["Presion"],
                            name="Presión", line=dict(color="#ec4899", width=2)),
                  row=3, col=2)
    
    fig.update_layout(
        height=900,
        showlegend=False,
        template="plotly_white",
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

# ============================================================================
# 8. PÁGINA: ALARMAS
# ============================================================================
elif pagina == " Alarmas":
    st.markdown("# 🔔 Centro de Alarmas")
    
    alertas = verificar_alarmas(df)
    
    if alertas:
        st.warning(f"⚠️ Se detectaron {len(alertas)} alarmas activas")
        for alerta in alertas:
            if alerta["tipo"] == "CRITICA":
                st.error(f"🚨 {alerta['msg']}")
            elif alerta["tipo"] == "ALTA":
                st.warning(f"️ {alerta['msg']}")
            else:
                st.info(f"ℹ️ {alerta['msg']}")
    else:
        st.success("✅ No hay alarmas activas. Todos los parámetros dentro de rangos normales.")
    
    # Tabla de umbrales
    st.markdown("### 📋 Umbrales configurados")
    df_umbral = pd.DataFrame({
        "Sensor": ["Temperatura", "Cloro", "Nivel", "Presión"],
        "Umbral": ["> 35°C", "> 4 ppm", "< 20%", "> 8 bar"],
        "Severidad": ["ALTA", "CRÍTICA", "MEDIA", "ALTA"]
    })
    st.dataframe(df_umbral, use_container_width=True)

# ============================================================================
# 9. PÁGINA: TEMPERATURA Y HUMEDAD
# ============================================================================
elif pagina == "🌡️ Temperatura y Humedad":
    st.markdown("# 🌡️ Temperatura y Humedad")
    st.markdown("Visualización de las últimas lecturas de temperatura y humedad.")
    
    ultima = df.iloc[-1]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Temperatura (°C)")
        gauge_temp = crear_gauge(
            ultima["Temperatura"], 0, 50, "Temperatura", "",
            [
                {"range": [0, 20], "color": "#bae6fd"},
                {"range": [20, 30], "color": "#86efac"},
                {"range": [30, 50], "color": "#fca5a5"}
            ]
        )
        st.plotly_chart(gauge_temp, use_container_width=True)
    
    with col2:
        st.subheader("Humedad (%)")
        gauge_hum = crear_gauge(
            ultima["Humedad"], 0, 100, "Humedad", "",
            [
                {"range": [0, 40], "color": "#dc2626"},
                {"range": [40, 60], "color": "#eab308"},
                {"range": [60, 100], "color": "#86efac"}
            ]
        )
        st.plotly_chart(gauge_hum, use_container_width=True)
    
    # Histórico
    st.markdown("### 📈 Histórico")
    fig_hist = go.Figure()
    fig_hist.add_trace(go.Scatter(
        x=df["created_at"], y=df["Temperatura"],
        name="Temperatura", line=dict(color="#ef4444", width=3),
        yaxis="y"
    ))
    fig_hist.add_trace(go.Scatter(
        x=df["created_at"], y=df["Humedad"],
        name="Humedad", line=dict(color="#3b82f6", width=3),
        yaxis="y2"
    ))
    fig_hist.update_layout(
        yaxis=dict(title="Temperatura (°C)", titlefont=dict(color="#ef4444")),
        yaxis2=dict(title="Humedad (%)", titlefont=dict(color="#3b82f6"), overlaying="y", side="right"),
        template="plotly_white",
        height=400
    )
    st.plotly_chart(fig_hist, use_container_width=True)

# ============================================================================
# 10. PÁGINA: DESCARGAS
# ============================================================================
elif pagina == " Descargas":
    st.markdown("# 📥 Descarga de Datos")
    
    df_export = df[["created_at", "Temperatura", "Humedad", 
                    "Caudal", "Cloro", "Nivel", "Altura", "Presion"]].copy()
    df_export = df_export.rename(columns={"created_at": "Fecha_Hora"})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df_export.to_csv(index=False).encode("utf-8")
        st.download_button("📄 CSV", csv,
                          f"acueducto_{datetime.now().strftime('%Y%m%d')}.csv",
                          "text/csv", use_container_width=True)
    
    with col2:
        json_data = df_export.to_json(orient="records", date_format="iso").encode("utf-8")
        st.download_button("📋 JSON", json_data,
                          f"acueducto_{datetime.now().strftime('%Y%m%d')}.json",
                          "application/json", use_container_width=True)
    
    with col3:
        st.markdown(f"**{len(df_export)} registros** disponibles")
    
    st.markdown("### 📋 Vista previa")
    st.dataframe(df_export.sort_values("Fecha_Hora", ascending=False), use_container_width=True)

# ============================================================================
# 11. AUTO-REFRESH
# ============================================================================
if auto_refresh:
    time.sleep(30)
    st.rerun()

# ============================================================================
# 12. FOOTER
# ============================================================================
st.markdown("---")
st.markdown("""


    

💧 Sistema de Monitoreo Acueducto · Programa Talento Tech 2025


    

ESP32 + DHT22 + Potenciómetros → ThingSpeak → GitHub → Streamlit




""", unsafe_allow_html=True)
