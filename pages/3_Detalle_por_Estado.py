"""
Página 3 · Detalle por estado (drill-down)
Responde: ¿por qué este estado pierde dinero y qué productos lo explican?
"""

import streamlit as st

from utils.data_loader import UMBRAL_DESCUENTO, calcular_kpis, cargar_datos, pct, resumen, usd
from utils.filters import aplicar_filtros, filtros_sidebar
from utils.plots import fig_ganancia_anual, fig_subcategorias

st.set_page_config(page_title="Detalle por estado · Superstore", page_icon="📊", layout="wide")

df = cargar_datos()
f = filtros_sidebar(df, mostrar_descuento=False)
df_f = aplicar_filtros(df, f, usar_descuento=False)

st.title("Detalle por estado")

if df_f.empty:
    st.warning("No hay datos para estos filtros.")
    st.stop()

# Por defecto se abre el estado que más dinero pierde con los filtros actuales
ranking = resumen(df_f, "State").sort_values("Ganancia")
estado = st.selectbox("Seleccione un estado (ordenados de mayor pérdida a mayor ganancia)", ranking["State"].tolist())

df_e = df_f[df_f["State"] == estado]
k = calcular_kpis(df_e)
alto = df_e[df_e["Discount"] > UMBRAL_DESCUENTO]

st.caption(f"Resumen › Excepción › **{estado}** · año {f['año']}")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Ventas", usd(k["ventas"]))
c2.metric("Ganancia", usd(k["ganancia"]))
c3.metric("Margen", pct(k["margen"]))
c4.metric("Ventas con descuento > 20 %", pct(alto["Sales"].sum() / k["ventas"], 0) if k["ventas"] else "—")

col1, col2 = st.columns(2)
with col1:
    with st.container(border=True):
        historico = aplicar_filtros(df, f, usar_año=False, usar_descuento=False)
        historico = historico[historico["State"] == estado]
        anios_perdida = (resumen(historico, "Año")["Ganancia"] < 0).sum()
        st.markdown("**¿Es un problema nuevo o crónico?** Ganancia anual del estado")
        st.caption(f"{estado} tuvo pérdida en **{anios_perdida} de {historico['Año'].nunique()} años**")
        fig_a = fig_ganancia_anual(historico)
        fig_a.update_layout(height=420)
        st.plotly_chart(fig_a, key="anual")

with col2:
    with st.container(border=True):
        st.markdown("**¿En qué productos?** Ganancia por subcategoría")
        st.caption("Pase el cursor para ver el descuento promedio de cada subcategoría")
        fig = fig_subcategorias(df_e)
        fig.update_layout(height=420)
        st.plotly_chart(fig, key="sub_estado")

with st.container(border=True):
    st.markdown("**Productos que más pierden en el estado**")
    productos = (df_e.groupby(["Product Name", "Sub-Category"])
                 .agg(Ventas=("Sales", "sum"), Ganancia=("Profit", "sum"), Descuento=("Discount", "mean"))
                 .reset_index().sort_values("Ganancia").head(10))
    st.dataframe(
        productos, hide_index=True,
        column_config={
            "Product Name": "Producto",
            "Sub-Category": "Subcategoría",
            "Ventas": st.column_config.NumberColumn(format="$ %.0f"),
            "Ganancia": st.column_config.NumberColumn(format="$ %.0f"),
            "Descuento": st.column_config.NumberColumn("Descuento prom.", format="percent"),
        },
    )
