"""
Página 2 · Descuentos
Amplía el Acto III: permite mover el umbral de descuento y ver qué estados
rompen la tendencia (descuento promedio vs margen).
"""

import streamlit as st

from utils.data_loader import analisis_descuento, cargar_datos, pct, resumen, usd
from utils.filters import aplicar_filtros, filtros_sidebar
from utils.plots import fig_bandas_descuento, fig_dispersion_estados

st.set_page_config(page_title="Descuentos · Superstore", page_icon="📊", layout="wide")

df = cargar_datos()
f = filtros_sidebar(df, mostrar_descuento=False)   # aquí el descuento se controla con el slider
df_f = aplicar_filtros(df, f, usar_descuento=False)

st.title("Excepción: el efecto de los descuentos")
st.caption(f"Año {f['año']} · mueva el umbral para encontrar a partir de qué descuento se pierde dinero")

if df_f.empty:
    st.warning("No hay datos para estos filtros.")
    st.stop()

umbral = st.slider("Umbral de descuento", min_value=0.05, max_value=0.50, value=0.20, step=0.05, format="%.2f",
                   help="Se analizan las ventas con descuento mayor a este valor (0,20 = 20 %).")

d = analisis_descuento(df_f, umbral)
alto = df_f[df_f["Discount"] > umbral]

c1, c2, c3 = st.columns(3)
c1.metric(f"Ventas con descuento > {umbral:.0%}", pct(d["pct_ventas"], 0), help="Porcentaje de las ventas totales")
c2.metric("Ganancia de esas ventas", usd(d["ganancia_alto"]))
c3.metric("Margen de esas ventas", pct(alto["Profit"].sum() / alto["Sales"].sum()) if not alto.empty else "—")

col1, col2 = st.columns([1, 1.4])
with col1:
    with st.container(border=True):
        st.markdown("**Ganancia por nivel de descuento**")
        bandas = resumen(df_f, "Banda_Descuento")
        con_perdida = bandas.loc[bandas["Ganancia"] < 0, "Banda_Descuento"].astype(str).tolist()
        st.caption(f"Niveles de descuento con pérdida: **{', '.join(con_perdida)}**" if con_perdida
                   else "Ningún nivel de descuento genera pérdida con estos filtros")
        st.plotly_chart(fig_bandas_descuento(df_f), key="bandas_p2")

with col2:
    with st.container(border=True):
        st.markdown("**Estados: descuento promedio vs margen** (tamaño = ventas)")
        est = resumen(df_f, "State")
        n_perdida = int(((est["Descuento_prom"] > umbral) & (est["Ganancia"] < 0)).sum())
        st.caption(f"Estados con descuento promedio mayor al umbral y pérdida: **{n_perdida}** · "
                   "pase el cursor para ver el detalle")
        st.plotly_chart(fig_dispersion_estados(df_f, umbral), key="dispersion")
