"""
Página 1 · Diagnóstico
Amplía el Acto II: ¿en qué regiones y subcategorías se pierde margen?
"""

import streamlit as st

from utils.data_loader import cargar_datos, pct, resumen, usd
from utils.filters import aplicar_filtros, filtros_sidebar
from utils.plots import fig_margen_region, fig_subcategorias

st.set_page_config(page_title="Diagnóstico · Superstore", page_icon="📊", layout="wide")

df = cargar_datos()
f = filtros_sidebar(df)
df_f = aplicar_filtros(df, f)

st.title("Diagnóstico: ¿dónde se pierde margen?")
st.caption(f"Año {f['año']} · pase el cursor sobre las barras para ver ventas, ganancia y descuento promedio")

if df_f.empty:
    st.warning("No hay datos para estos filtros.")
    st.stop()

col1, col2 = st.columns([1, 1.3])

with col1:
    with st.container(border=True):
        reg = resumen(df_f, "Region").sort_values("Margen")
        st.markdown("**Margen por región** (línea punteada = meta 15 %)")
        st.caption(f"La región más débil es **{reg.iloc[0]['Region']}** con un margen de **{pct(reg.iloc[0]['Margen'])}**")
        st.plotly_chart(fig_margen_region(df_f), key="region")

    with st.container(border=True):
        cat = resumen(df_f, "Category").sort_values("Margen")
        st.markdown("**Margen por categoría**")
        c1, c2, c3 = st.columns(3)
        for col, (_, fila) in zip([c1, c2, c3], cat.iterrows()):
            col.metric(fila["Category"], pct(fila["Margen"]), help=f"Ventas {usd(fila['Ventas'])}")

with col2:
    with st.container(border=True):
        sub = resumen(df_f, "Sub-Category")
        negativas = sub[sub["Ganancia"] < 0].sort_values("Ganancia")
        st.markdown("**Ganancia por subcategoría** (en rojo, las que pierden dinero)")
        if negativas.empty:
            st.caption("Ninguna subcategoría pierde dinero con estos filtros.")
        else:
            st.caption(f"**{len(negativas)} subcategorías** venden con pérdida; la peor es "
                       f"**{negativas.iloc[0]['Sub-Category']} ({usd(negativas.iloc[0]['Ganancia'])})**")
        st.plotly_chart(fig_subcategorias(df_f), key="subcategorias")
