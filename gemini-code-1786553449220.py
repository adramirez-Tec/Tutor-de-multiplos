import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from google import genai
from google.genai import types

# Configuración inicial de la página
st.set_page_config(
    page_title="Valuador por Múltiplos IA",
    page_icon="📈",
    layout="wide"
)

st.title("📈 Valuación por Múltiplos con Gem AI")
st.markdown("Calcula el valor implícito de tu empresa utilizando comparables de mercado y genera un informe analítico detallado.")

# Sidebar - Configuración de API Key e Instrucción del Gem
with st.sidebar:
    st.header("⚙️ Configuración")
    api_key = st.text_input("Gemini API Key", type="password", help="Obtén tu API key en Google AI Studio")
    
    st.divider()
    st.subheader("Prompt del Gem (System Instruction)")
    
    default_prompt = """Eres un analista senior de Banca de Inversión especializado en valuación por múltiplos comparables.
Tu objetivo es analizar los datos financieros de la empresa objetivo y los múltiplos del sector.
Genera un informe profesional estructurado que incluya:
1. Resumen Ejecutivo de la Valuación.
2. Comparativa entre los métodos (EV/EBITDA, P/E, P/S) y cuál es más representativo para el sector.
3. Rango de precio por acción (Escenario Pesimista, Base y Optimista).
4. Principales riesgos, sesgos del método de múltiplos y recomendaciones para afinar la valuación."""

    gem_instruction = st.text_area("Instrucciones del Gem", value=default_prompt, height=220)

# Layout principal
col_left, col_right = st.columns([1, 1], gap="large")

with col_left:
    st.subheader("1. Métricas de la Empresa Objetivo")
    col_a, col_b = st.columns(2)
    with col_a:
        ticker = st.text_input("Nombre / Ticker", value="TechCorp Inc.")
        ebitda = st.number_input("EBITDA ($ M)", value=15.0, step=1.0)
        ventas = st.number_input("Ventas Totales ($ M)", value=50.0, step=1.0)
    with col_b:
        net_income = st.number_input("Utilidad Neta ($ M)", value=8.0, step=1.0)
        net_debt = st.number_input("Deuda Neta ($ M)", value=5.0, step=1.0)
        shares = st.number_input("Acciones en circulación (M)", value=10.0, step=0.5)

    st.subheader("2. Múltiplos Promedio del Sector")
    col_c, col_d, col_e = st.columns(3)
    with col_c:
        mult_ev_ebitda = st.number_input("EV/EBITDA (x)", value=10.0, step=0.5)
    with col_d:
        mult_pe = st.number_input("P/E (x)", value=15.0, step=0.5)
    with col_e:
        mult_ps = st.number_input("P/S (x)", value=2.5, step=0.1)

# Cálculos Matemáticos directos
ev_ebitda_val = ebitda * mult_ev_ebitda
eq_val_ebitda = ev_ebitda_val - net_debt
price_ebitda = max(0.0, eq_val_ebitda / shares) if shares > 0 else 0

price_pe = max(0.0, (net_income * mult_pe) / shares) if shares > 0 else 0

ev_ps_val = ventas * mult_ps
eq_val_ps = ev_ps_val - net_debt
price_ps = max(0.0, eq_val_ps / shares) if shares > 0 else 0

avg_price = (price_ebitda + price_pe + price_ps) / 3

with col_right:
    st.subheader("3. Rangos de Precio Implícito por Acción")
    
    # Gráfico de barras horizontales (Football Field Chart simplificado)
    fig = go.Figure()
    
    methods = ['EV/EBITDA', 'P/E (Utilidad)', 'P/S (Ventas)']
    prices = [price_ebitda, price_pe, price_ps]
    
    fig.add_trace(go.Bar(
        x=prices,
        y=methods,
        orientation='h',
        marker=dict(color=['#2b5c8f', '#4682b4', '#6baed6']),
        text=[f"${p:.2f}" for p in prices],
        textposition='auto'
    ))
    
    fig.add_vline(x=avg_price, line_dash="dash", line_color="red", annotation_text=f"Promedio: ${avg_price:.2f}")
    fig.update_layout(height=280, margin=dict(l=20, r=20, t=30, b=20), xaxis_title="Precio por Acción ($)")
    
    st.plotly_chart(fig, use_container_width=True)

    # Tarjetas informativas
    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Precio Promedio", f"${avg_price:.2f}")
    kpi2.metric("EV (vía EBITDA)", f"${ev_ebitda_val:.1f} M")
    kpi3.metric("Equity Value", f"${eq_val_ebitda:.1f} M")

st.divider()

# Botón para ejecutar el Gem
if st.button("🚀 Generar Informe de Valuación con IA", type="primary", use_container_width=True):
    if not api_key:
        st.error("⚠️ Por favor ingresa tu API Key de Gemini en la barra lateral izquierda.")
    else:
        client = genai.Client(api_key=api_key)
        
        user_prompt = f"""
Por favor realiza la valuación completa para {ticker} con la siguiente información:

DATOS FINANCIEROS:
- EBITDA: ${ebitda:.2f} M
- Ventas: ${ventas:.2f} M
- Utilidad Neta: ${net_income:.2f} M
- Deuda Neta: ${net_debt:.2f} M
- Acciones en circulación: {shares:.2f} M

MÚLTIPLOS Y PRECIOS IMPLÍCITOS CALCULADOS:
1. Múltiplo EV/EBITDA ({mult_ev_ebitda}x):
   - EV Implícito: ${ev_ebitda_val:.2f} M
   - Precio por acción implícito: ${price_ebitda:.2f}
2. Múltiplo P/E ({mult_pe}x):
   - Precio por acción implícito: ${price_pe:.2f}
3. Múltiplo P/S ({mult_ps}x):
   - Precio por acción implícito: ${price_ps:.2f}

Precio Promedio ponderado básico: ${avg_price:.2f}
"""
        with st.spinner("El Gem está analizando la estructura financiera y generando el dictamen..."):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=gem_instruction,
                        temperature=0.2
                    )
                )
                
                st.subheader("📄 Dictamen del Gem de Valuación")
                st.markdown(response.text)
                
            except Exception as e:
                st.error(f"Ocurrió un error al conectar con Gemini API: {str(e)}")