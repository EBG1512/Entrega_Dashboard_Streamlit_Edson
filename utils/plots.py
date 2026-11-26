"""
plots.py
--------
Funciones que construyen y devuelven las gráficas (Plotly) del dashboard.

Las páginas solo llaman a estas funciones y muestran la figura con
st.plotly_chart(fig). Así el código de cada página queda corto y legible.

Paleta (color con propósito):
  rojo  = pérdida o bajo la meta   ámbar = alerta
  verde = sobre la meta            gris  = contexto
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_loader import META_MARGEN, ORDEN_BANDAS, resumen, usd

ROJO, AMBAR, VERDE, GRIS, TINTA = "#C0392B", "#D68910", "#1E8449", "#9CA3AF", "#1F2937"
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]


def _estilo(fig: go.Figure, alto: int = 320) -> go.Figure:
    """Estilo común: fondo limpio, márgenes pequeños y fuente legible."""
    fig.update_layout(
        height=alto,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(size=13, color=TINTA),
        hoverlabel=dict(bgcolor="#111827", font_color="white", font_size=13),
        showlegend=False,
    )
    return fig


def color_margen(m: float) -> str:
    if m < 0:
        return ROJO
    if m < META_MARGEN:
        return AMBAR
    return VERDE


# ------------------------------------------------------------------
# ACTO I · Situación
# ------------------------------------------------------------------
def fig_bala(actual: float, meta: float = META_MARGEN, potencial: float | None = None, alto: int = 110) -> go.Figure:
    """Gráfico de bala: margen actual vs meta (y opcionalmente el potencial)."""
    maximo = max(0.22, (potencial or 0) + 0.02, actual + 0.02)
    pasos = [dict(range=[0, meta], color="#F3F4F6"), dict(range=[meta, maximo], color="#E5E7EB")]
    if potencial is not None:
        pasos.append(dict(range=[0, potencial], color="rgba(30,132,73,0.30)"))
    fig = go.Figure(go.Indicator(
        mode="gauge",
        value=actual * 100,
        gauge=dict(
            shape="bullet",
            axis=dict(range=[min(0, actual * 100), maximo * 100], ticksuffix=" %"),
            bar=dict(color=color_margen(actual), thickness=0.45),
            steps=[dict(range=[s["range"][0] * 100, s["range"][1] * 100], color=s["color"]) for s in pasos],
            threshold=dict(line=dict(color=TINTA, width=4), thickness=0.9, value=meta * 100),
        ),
        domain=dict(x=[0, 1], y=[0, 1]),
    ))
    fig.update_layout(height=alto, margin=dict(l=15, r=25, t=10, b=25), paper_bgcolor="white")
    return fig


def fig_tendencia_margen(df_actual: pd.DataFrame, df_anterior: pd.DataFrame, año: int) -> go.Figure:
    """Línea de tendencia del margen mensual del año vs el año anterior y la meta."""
    fig = go.Figure()
    for datos, nombre, color, ancho in [(df_anterior, str(año - 1), "#CBD5E1", 2), (df_actual, str(año), TINTA, 3)]:
        if datos.empty:
            continue
        m = resumen(datos.assign(MesNum=datos["Order Date"].dt.month), "MesNum")
        es_actual = nombre == str(año)
        fig.add_trace(go.Scatter(
            x=[MESES[i - 1] for i in m["MesNum"]],
            y=m["Margen"] * 100,
            name=nombre,
            mode="lines+markers" if es_actual else "lines",
            line=dict(color=color, width=ancho),
            marker=dict(size=9, color=[ROJO if v < META_MARGEN else TINTA for v in m["Margen"]]),
            customdata=m[["Ventas", "Ganancia"]].values,
            hovertemplate=(f"<b>%{{x}} {nombre}</b><br>Margen: %{{y:.1f}} %"
                           "<br>Ventas: USD %{customdata[0]:,.0f}<br>Ganancia: USD %{customdata[1]:,.0f}<extra></extra>"),
        ))
    fig.add_hline(y=META_MARGEN * 100, line_dash="dash", line_color=TINTA,
                  annotation_text="Meta 15 %", annotation_position="top right")
    fig.update_yaxes(ticksuffix=" %", gridcolor="#E5E7EB", zeroline=True, zerolinecolor="#9CA3AF")
    fig.update_xaxes(categoryorder="array", categoryarray=MESES)
    _estilo(fig, 300)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.12, x=0))
    return fig


# ------------------------------------------------------------------
# ACTO II · Diagnóstico
# ------------------------------------------------------------------
def fig_mapa_calor(df: pd.DataFrame) -> go.Figure:
    """Mapa de calor del margen: región × categoría."""
    t = resumen(df, ["Region", "Category"])
    margen = t.pivot(index="Region", columns="Category", values="Margen")
    ventas = t.pivot(index="Region", columns="Category", values="Ventas")
    ganancia = t.pivot(index="Region", columns="Category", values="Ganancia")
    texto = margen.map(lambda v: f"{v * 100:.1f} %".replace(".", ",") if pd.notna(v) else "")
    fig = go.Figure(go.Heatmap(
        z=margen.values * 100,
        x=margen.columns,
        y=margen.index,
        text=texto.values,
        texttemplate="%{text}",
        textfont=dict(size=15),
        customdata=np.dstack([ventas.values, ganancia.values]),
        colorscale=[[0, "#C0392B"], [0.45, "#FAD7A0"], [0.6, "#FCF3CF"], [1, "#58D68D"]],
        zmid=META_MARGEN * 100, zmin=-20, zmax=35,
        xgap=4, ygap=4, showscale=False,
        hovertemplate=("<b>%{y} · %{x}</b><br>Margen: %{text}"
                       "<br>Ventas: USD %{customdata[0]:,.0f}<br>Ganancia: USD %{customdata[1]:,.0f}<extra></extra>"),
    ))
    fig.update_yaxes(autorange="reversed")
    return _estilo(fig, 300)


def fig_margen_region(df: pd.DataFrame) -> go.Figure:
    """Barras horizontales ordenadas: margen por región con línea de meta."""
    t = resumen(df, "Region").sort_values("Margen")
    fig = go.Figure(go.Bar(
        x=t["Margen"] * 100, y=t["Region"], orientation="h",
        marker_color=[color_margen(m) for m in t["Margen"]],
        text=[f"{m * 100:.1f} %".replace(".", ",") for m in t["Margen"]], textposition="outside",
        customdata=t[["Ventas", "Ganancia", "Descuento_prom"]].values,
        hovertemplate=("<b>%{y}</b><br>Margen: %{x:.1f} %<br>Ventas: USD %{customdata[0]:,.0f}"
                       "<br>Ganancia: USD %{customdata[1]:,.0f}<br>Descuento promedio: %{customdata[2]:.0%}<extra></extra>"),
    ))
    fig.add_vline(x=META_MARGEN * 100, line_dash="dash", line_color=TINTA, annotation_text="Meta")
    fig.update_xaxes(ticksuffix=" %", gridcolor="#E5E7EB",
                     range=[min(0, t["Margen"].min() * 130), max(META_MARGEN, t["Margen"].max()) * 130])
    return _estilo(fig, 280)


def fig_subcategorias(df: pd.DataFrame) -> go.Figure:
    """Ganancia por subcategoría (las negativas en rojo)."""
    t = resumen(df, "Sub-Category").sort_values("Ganancia")
    fig = go.Figure(go.Bar(
        x=t["Ganancia"], y=t["Sub-Category"], orientation="h",
        marker_color=[ROJO if g < 0 else GRIS for g in t["Ganancia"]],
        customdata=t[["Ventas", "Margen", "Descuento_prom"]].values,
        hovertemplate=("<b>%{y}</b><br>Ganancia: USD %{x:,.0f}<br>Ventas: USD %{customdata[0]:,.0f}"
                       "<br>Margen: %{customdata[1]:.1%}<br>Descuento promedio: %{customdata[2]:.0%}<extra></extra>"),
    ))
    fig.update_xaxes(tickprefix="USD ", gridcolor="#E5E7EB")
    return _estilo(fig, 480)


# ------------------------------------------------------------------
# ACTO III · Excepción (descuentos)
# ------------------------------------------------------------------
def fig_bandas_descuento(df: pd.DataFrame) -> go.Figure:
    """Ganancia por nivel de descuento: muestra el punto de quiebre."""
    t = resumen(df, "Banda_Descuento")
    t["Banda_Descuento"] = pd.Categorical(t["Banda_Descuento"], ORDEN_BANDAS, ordered=True)
    t = t.sort_values("Banda_Descuento")
    pct_ventas = t["Ventas"] / t["Ventas"].sum()
    fig = go.Figure(go.Bar(
        x=t["Banda_Descuento"].astype(str), y=t["Ganancia"],
        marker_color=[VERDE if g > 0 else ROJO for g in t["Ganancia"]],
        text=[usd(g) for g in t["Ganancia"]], textposition="outside",
        customdata=pd.DataFrame({"v": t["Ventas"], "p": pct_ventas, "m": t["Margen"]}).values,
        hovertemplate=("<b>%{x}</b><br>Ganancia: USD %{y:,.0f}<br>Ventas: USD %{customdata[0]:,.0f}"
                       " (%{customdata[1]:.0%} del total)<br>Margen: %{customdata[2]:.1%}<extra></extra>"),
    ))
    fig.add_hline(y=0, line_color=TINTA)
    fig.update_yaxes(tickprefix="USD ", gridcolor="#E5E7EB")
    return _estilo(fig, 300)


def fig_estados_perdida(df_alto: pd.DataFrame, top: int = 5) -> go.Figure:
    """Estados con mayor pérdida en ventas con descuento profundo."""
    t = resumen(df_alto, "State").sort_values("Ganancia").head(top).iloc[::-1]
    t = t[t["Ganancia"] < 0]
    fig = go.Figure(go.Bar(
        x=-t["Ganancia"], y=t["State"], orientation="h", marker_color=ROJO,
        text=[usd(g) for g in t["Ganancia"]], textposition="outside", cliponaxis=False,
        customdata=t[["Ventas", "Descuento_prom", "Pedidos"]].values,
        hovertemplate=("<b>%{y}</b><br>Pérdida: USD %{x:,.0f}<br>Ventas con descuento > 20 %: USD %{customdata[0]:,.0f}"
                       "<br>Descuento promedio: %{customdata[1]:.0%}<br>Pedidos: %{customdata[2]}"
                       "<br><i>Vea el detalle en la página 'Detalle por estado'</i><extra></extra>"),
    ))
    fig.update_xaxes(tickprefix="USD ", gridcolor="#E5E7EB", title="Pérdida", range=[0, max(-t["Ganancia"].min() * 1.3, 1)])
    return _estilo(fig, 300)


def fig_dispersion_estados(df: pd.DataFrame, umbral: float) -> go.Figure:
    """Cada burbuja es un estado: descuento promedio vs margen (tamaño = ventas)."""
    t = resumen(df, "State")
    t["Color"] = ["Descuento > umbral" if d > umbral else "Descuento ≤ umbral" for d in t["Descuento_prom"]]
    fig = px.scatter(
        t, x="Descuento_prom", y="Margen", size="Ventas", color="Color", hover_name="State",
        color_discrete_map={"Descuento > umbral": ROJO, "Descuento ≤ umbral": "#5DADE2"},
        custom_data=["Ventas", "Ganancia"], size_max=45,
    )
    fig.update_traces(hovertemplate=("<b>%{hovertext}</b><br>Descuento promedio: %{x:.0%}<br>Margen: %{y:.1%}"
                                     "<br>Ventas: USD %{customdata[0]:,.0f}<br>Ganancia: USD %{customdata[1]:,.0f}<extra></extra>"))
    fig.add_vline(x=umbral, line_dash="dash", line_color=ROJO, annotation_text=f"Umbral {umbral:.0%}")
    fig.add_hline(y=0, line_color=TINTA)
    fig.update_xaxes(tickformat=".0%", title="Descuento promedio del estado", gridcolor="#E5E7EB")
    fig.update_yaxes(tickformat=".0%", title="Margen", gridcolor="#E5E7EB")
    _estilo(fig, 430)
    fig.update_layout(showlegend=True, legend=dict(orientation="h", y=1.08, x=0, title=None))
    return fig


# ------------------------------------------------------------------
# Detalle y comparaciones
# ------------------------------------------------------------------
def fig_ganancia_anual(df: pd.DataFrame) -> go.Figure:
    """Ganancia por año (para ver si un problema es nuevo o crónico)."""
    t = resumen(df, "Año")
    fig = go.Figure(go.Bar(
        x=t["Año"].astype(str), y=t["Ganancia"],
        marker_color=[VERDE if g > 0 else ROJO for g in t["Ganancia"]],
        text=[usd(g) for g in t["Ganancia"]], textposition="outside",
        customdata=t[["Ventas", "Margen"]].values,
        hovertemplate="<b>%{x}</b><br>Ganancia: USD %{y:,.0f}<br>Ventas: USD %{customdata[0]:,.0f}<br>Margen: %{customdata[1]:.1%}<extra></extra>",
    ))
    fig.add_hline(y=0, line_color=TINTA)
    fig.update_yaxes(tickprefix="USD ", gridcolor="#E5E7EB")
    return _estilo(fig, 300)


def fig_cambios(t: pd.DataFrame, columna: str) -> go.Figure:
    """Barras divergentes con el cambio de ganancia entre dos períodos."""
    fig = go.Figure(go.Bar(
        x=t["Cambio"], y=t[columna], orientation="h",
        marker_color=[VERDE if c > 0 else ROJO for c in t["Cambio"]],
        customdata=t[["Ganancia_actual", "Ganancia_anterior"]].values,
        hovertemplate=("<b>%{y}</b><br>Cambio: USD %{x:,.0f}<br>Período actual: USD %{customdata[0]:,.0f}"
                       "<br>Período anterior: USD %{customdata[1]:,.0f}<extra></extra>"),
    ))
    fig.add_vline(x=0, line_color=TINTA)
    fig.update_xaxes(tickprefix="USD ", gridcolor="#E5E7EB")
    return _estilo(fig, 360)
