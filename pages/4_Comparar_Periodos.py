"""
Página 4 · Comparar períodos
Permite elegir un rango de fechas y compararlo con el período anterior para
encontrar automáticamente qué subcategorías y estados mejoraron o empeoraron.
"""

from datetime import date

import pandas as pd
import streamlit as st

from utils.data_loader import calcular_kpis, cargar_datos, pct, resumen, usd
from utils.filters import aplicar_filtros, filtros_sidebar
from utils.plots import fig_cambios

st.set_page_config(page_title="Comparar períodos · Superstore", page_icon="📊", layout="wide")

df = cargar_datos()
f = filtros_sidebar(df, mostrar_año=False)              # aquí el tiempo se controla con el rango de fechas
df_f = aplicar_filtros(df, f, usar_año=False)

st.title("Comparar períodos: ¿qué mejoró y qué empeoró?")

fecha_min, fecha_max = df["Order Date"].min().date(), df["Order Date"].max().date()
c1, c2 = st.columns([2, 1])
rango = c1.date_input("Período a analizar", value=(date(fecha_max.year, 10, 1), fecha_max),
                      min_value=fecha_min, max_value=fecha_max, format="DD/MM/YYYY")
comparar_con = c2.radio("Comparar con", ["Mismo período del año anterior", "Período inmediatamente anterior"])

if not isinstance(rango, tuple) or len(rango) != 2:
    st.info("Seleccione la fecha inicial y la fecha final del período.")
    st.stop()

inicio, fin = pd.Timestamp(rango[0]), pd.Timestamp(rango[1])
if comparar_con.startswith("Mismo"):
    inicio_ant, fin_ant = inicio - pd.DateOffset(years=1), fin - pd.DateOffset(years=1)
else:
    dias = (fin - inicio).days + 1
    inicio_ant, fin_ant = inicio - pd.Timedelta(days=dias), inicio - pd.Timedelta(days=1)

actual = df_f[df_f["Order Date"].between(inicio, fin)]
anterior = df_f[df_f["Order Date"].between(inicio_ant, fin_ant)]

st.caption(f"Actual: {inicio:%d/%m/%Y} – {fin:%d/%m/%Y}  ·  Anterior: {inicio_ant:%d/%m/%Y} – {fin_ant:%d/%m/%Y}")

if actual.empty or anterior.empty:
    st.warning("Uno de los dos períodos no tiene datos. Ajuste el rango de fechas.")
    st.stop()

k, k_ant = calcular_kpis(actual), calcular_kpis(anterior)
m1, m2, m3 = st.columns(3)
m1.metric("Ventas", usd(k["ventas"]), f"{k['ventas'] / k_ant['ventas'] - 1:+.0%}")
cambio = k["ganancia"] - k_ant["ganancia"]
m2.metric("Ganancia", usd(k["ganancia"]), f"{'+' if cambio >= 0 else '-'}USD {abs(cambio) / 1000:.1f} K".replace(".", ","))
m3.metric("Margen", pct(k["margen"]), f"{(k['margen'] - k_ant['margen']) * 100:+.1f} pts".replace(".", ","))


def tabla_cambios(columna: str) -> pd.DataFrame:
    a = resumen(actual, columna)[[columna, "Ganancia"]].rename(columns={"Ganancia": "Ganancia_actual"})
    b = resumen(anterior, columna)[[columna, "Ganancia"]].rename(columns={"Ganancia": "Ganancia_anterior"})
    t = a.merge(b, on=columna, how="outer").fillna(0)
    t["Cambio"] = t["Ganancia_actual"] - t["Ganancia_anterior"]
    t = t.sort_values("Cambio")
    return pd.concat([t.head(5), t.tail(5)]).drop_duplicates(columna)


col1, col2 = st.columns(2)
for col, columna, titulo in [(col1, "Sub-Category", "subcategorías"), (col2, "State", "estados")]:
    with col:
        with st.container(border=True):
            t = tabla_cambios(columna)
            st.markdown(f"**Las 5 {titulo} que más mejoraron y las 5 que más empeoraron**")
            st.caption(f"Mayor caída: **{t.iloc[0][columna]} ({usd(t.iloc[0]['Cambio'])})** · "
                       f"mayor mejora: **{t.iloc[-1][columna]} ({usd(t.iloc[-1]['Cambio'])})**")
            st.plotly_chart(fig_cambios(t, columna), key=f"cambios_{columna}")
