"""
dash_superstore.py  ·  Página principal (centralizador)
--------------------------------------------------------
Implementa en Streamlit el boceto de la Actividad 2:
"¿Estamos creciendo con rentabilidad?" – Panel del Director Comercial Nacional.

La historia se lee de arriba hacia abajo y de izquierda a derecha:
  Acto I   · Situación    -> margen vs meta y tendencia
  Acto II  · Diagnóstico  -> mapa de calor región × categoría
  Acto III · Excepción    -> ganancia por nivel de descuento y estados con pérdida
  Acto IV  · Acción       -> margen actual vs meta vs potencial

Ejecutar en la terminal (desde la carpeta del proyecto):
    streamlit run dash_superstore.py
"""

import streamlit as st

from utils.data_loader import (META_MARGEN, analisis_descuento, calcular_kpis,
                               cargar_datos, pct, resumen, usd,
                               usd_corto)
from utils.filters import aplicar_filtros, filtros_sidebar
from utils.plots import (fig_bala, fig_bandas_descuento, fig_estados_perdida,
                         fig_mapa_calor, fig_tendencia_margen)

# ------------------------------------------------------------------
# 1. Configuración general de la página
# ------------------------------------------------------------------
st.set_page_config(page_title="Superstore · Rentabilidad comercial", page_icon="📊", layout="wide")

# ------------------------------------------------------------------
# 2. Carga de datos y filtros
# ------------------------------------------------------------------
df = cargar_datos()
f = filtros_sidebar(df)

df_f = aplicar_filtros(df, f)                                       # todos los filtros
df_base = aplicar_filtros(df, f, usar_descuento=False)              # sin el filtro de descuento
df_ant = aplicar_filtros(df, f, año=f["año"] - 1)                   # año anterior (para variaciones)
df_ant_base = aplicar_filtros(df, f, usar_descuento=False, año=f["año"] - 1)

if df_f.empty:
    st.warning("No hay datos para la combinación de filtros seleccionada. Ajuste los filtros de la barra lateral.")
    st.stop()

k = calcular_kpis(df_f)
k_ant = calcular_kpis(df_ant) if not df_ant.empty else None
desc = analisis_descuento(df_base)

# ------------------------------------------------------------------
# 3. Encabezado
# ------------------------------------------------------------------
st.title("¿Estamos creciendo con rentabilidad?")
st.caption(f"Superstore · Panel del Director Comercial Nacional · revisión mensual · año {f['año']}")
if f["descuento"] != "Todos":
    st.info(f"Filtro clave activo: **descuento {f['descuento'].lower()}**. Los KPIs muestran solo esas ventas.")

# ------------------------------------------------------------------
# FILA 1 · ACTO I – Situación
# ------------------------------------------------------------------
col1, col2 = st.columns([1.25, 1.6])

with col1:
    with st.container(border=True):
        st.markdown("**1 · Situación** — ¿Cómo estamos hoy en lo crítico?")
        m1, m2, m3 = st.columns([1, 1.1, 1.1])
        delta_margen = f"{(k['margen'] - k_ant['margen']) * 100:+.1f} pts".replace(".", ",") if k_ant else None
        delta_ventas = f"{k['ventas'] / k_ant['ventas'] - 1:+.0%}" if k_ant else None
        delta_ganancia = f"{k['ganancia'] / k_ant['ganancia'] - 1:+.0%}" if k_ant and k_ant["ganancia"] > 0 else None
        m1.metric("Margen", pct(k["margen"]), delta_margen, help="Ganancia ÷ Ventas. Variación vs año anterior.")
        m2.metric("Ventas", usd_corto(k["ventas"]), delta_ventas)
        m3.metric("Ganancia", usd_corto(k["ganancia"]), delta_ganancia)
        st.plotly_chart(fig_bala(k["margen"]), key="bala_situacion")
        brecha = (k["margen"] - META_MARGEN) * 100
        if brecha < 0:
            st.markdown(f":red[**Faltan {abs(brecha):.1f} puntos para la meta del 15 %.**]".replace(".", ",", 1))
        else:
            st.markdown(f":green[**Se supera la meta del 15 % por {brecha:.1f} puntos.**]".replace(".", ",", 1))

with col2:
    with st.container(border=True):
        st.markdown("**Tendencia del margen vs meta** — ¿El margen se acerca o se aleja de la meta?")
        st.caption("Tendencia del margen mensual · puntos rojos = meses bajo la meta")
        st.plotly_chart(fig_tendencia_margen(df_f, df_ant, f["año"]), key="tendencia")

# ------------------------------------------------------------------
# FILA 2 · ACTO II – Diagnóstico  |  ACTO III – Excepción
# ------------------------------------------------------------------
col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        celdas = resumen(df_f, ["Region", "Category"]).sort_values("Margen")
        peor = celdas.iloc[0]
        st.markdown("**2 · Diagnóstico** — ¿Dónde se está perdiendo margen?")
        st.caption(f"Mapa de calor del margen · la combinación más débil es "
                   f"**{peor['Category']} en {peor['Region']} ({pct(peor['Margen'])})**")
        st.plotly_chart(fig_mapa_calor(df_f), key="mapa_calor")

with col4:
    with st.container(border=True):
        st.markdown("**3 · Excepción** — ¿Por qué? Ganancia por nivel de descuento")
        st.caption(f"Ventas con descuento > 20 %: **{pct(desc['pct_ventas'], 0)} de lo vendido** "
                   f"y una ganancia de **{usd(desc['ganancia_alto'])}**")
        st.plotly_chart(fig_bandas_descuento(df_base), key="bandas")

# ------------------------------------------------------------------
# FILA 3 · ACTO III (aislado con el filtro) | ACTO IV – Acción
# ------------------------------------------------------------------
col5, col6 = st.columns(2)

df_alto = df_base[df_base["Descuento_Alto"]]
estados = resumen(df_alto, "State").sort_values("Ganancia")
perdida_total = estados.loc[estados["Ganancia"] < 0, "Ganancia"].sum()
top4 = estados[estados["Ganancia"] < 0].head(4)          # hasta 4 estados con pérdida
participacion_top4 = top4["Ganancia"].sum() / perdida_total if perdida_total < 0 else 0

with col5:
    with st.container(border=True):
        st.markdown("**3 · Excepción aislada** — ¿Qué estados pierden más en ventas con descuento > 20 %?")
        if perdida_total < 0:
            st.caption(f"Los {len(top4)} estados con mayor pérdida concentran el **{pct(participacion_top4, 0)}** "
                       "de la pérdida por descuentos mayores al 20 %")
        else:
            st.caption("Con estos filtros, las ventas con descuento mayor al 20 % no generan pérdida")
        if df_alto.empty:
            st.info("No hay ventas con descuento mayor al 20 % para estos filtros.")
        else:
            st.plotly_chart(fig_estados_perdida(df_alto), key="estados")

with col6:
    with st.container(border=True):
        st.markdown("**4 · Acción** — Margen actual vs meta: ¿cuál es el siguiente paso?")
        k_base = calcular_kpis(df_base)
        st.caption(f"Margen de hoy ({pct(k_base['margen'])}) vs meta (15 %) vs potencial "
                   f"si las ventas con descuento > 20 % no generaran pérdida ({pct(desc['margen_potencial'])})")
        st.plotly_chart(fig_bala(k_base["margen"], potencial=desc["margen_potencial"]), key="bala_accion")
        # Las recomendaciones se construyen según lo que muestran los datos filtrados
        acciones = []
        if k_base["margen"] >= META_MARGEN:
            acciones.append("🟢 El margen cumple la meta: mantener el seguimiento mensual.")
        if desc["ganancia_alto"] < 0:
            acciones.append(f"🔴 **Revisar los descuentos mayores al 20 %:** generan una pérdida de {usd(desc['ganancia_alto'])}.")
            acciones.append(f"🔴 **Priorizar:** {', '.join(top4['State'])} ({pct(participacion_top4, 0)} de esa pérdida).")
        else:
            acciones.append("🟢 Los descuentos mayores al 20 % no generan pérdida con estos filtros.")
        sub = resumen(df_base, "Sub-Category")
        sub_neg = sub[sub["Ganancia"] < 0].sort_values("Ganancia")["Sub-Category"].head(3).tolist()
        if sub_neg:
            acciones.append(f"🟠 Revisar precios de las subcategorías con pérdida: {', '.join(sub_neg)}.")
        st.markdown("\n".join(f"- {a}" for a in acciones))
