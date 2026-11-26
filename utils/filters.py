"""
filters.py
----------
Filtros del dashboard (barra lateral) y la función que los aplica.

Cada página llama a `filtros_sidebar()` para dibujar los mismos filtros y a
`aplicar_filtros()` para obtener el DataFrame filtrado. Así no se repite
código en cada página.

Los valores elegidos se guardan en st.session_state para que se mantengan
al pasar de una página a otra.
"""

import pandas as pd
import streamlit as st

OPCIONES_DESCUENTO = ["Todos", "Hasta 20 %", "Mayor a 20 %"]


def _inicializar_estado(df: pd.DataFrame) -> None:
    """Define los valores por defecto la primera vez que se abre el dashboard."""
    defaults = {
        "f_año": int(df["Año"].max()),
        "f_regiones": sorted(df["Region"].unique()),
        "f_categorias": sorted(df["Category"].unique()),
        "f_descuento": "Todos",
    }
    for clave, valor in defaults.items():
        if clave not in st.session_state:
            st.session_state[clave] = valor
        else:
            # Truco recomendado por Streamlit para conservar el valor entre páginas
            st.session_state[clave] = st.session_state[clave]


def filtros_sidebar(df: pd.DataFrame, mostrar_año: bool = True, mostrar_descuento: bool = True) -> dict:
    """Dibuja los filtros globales en la barra lateral y devuelve lo elegido."""
    _inicializar_estado(df)

    st.sidebar.header("Filtros")

    if mostrar_año:
        st.sidebar.selectbox(
            "Año",
            sorted(df["Año"].unique()),
            key="f_año",
            help="Año que se analiza. Las variaciones se comparan con el año anterior.",
        )

    st.sidebar.multiselect("Región", sorted(df["Region"].unique()), key="f_regiones")
    st.sidebar.multiselect("Categoría", sorted(df["Category"].unique()), key="f_categorias")

    if mostrar_descuento:
        st.sidebar.radio(
            "Descuento (filtro clave)",
            OPCIONES_DESCUENTO,
            key="f_descuento",
            help="Seleccione 'Mayor a 20 %' para aislar las ventas con descuento profundo.",
        )

    st.sidebar.caption("Meta de margen: 15 % · Umbral de descuento: 20 %")

    return {
        "año": st.session_state["f_año"],
        "regiones": st.session_state["f_regiones"],
        "categorias": st.session_state["f_categorias"],
        "descuento": st.session_state["f_descuento"] if mostrar_descuento else "Todos",
    }


def aplicar_filtros(df: pd.DataFrame, f: dict, usar_año: bool = True, usar_descuento: bool = True,
                    año: int | None = None) -> pd.DataFrame:
    """Devuelve el DataFrame filtrado.

    usar_año=False       -> ignora el filtro de año (útil para tendencias de varios años).
    usar_descuento=False -> ignora el filtro de descuento (útil para comparar con/sin descuento).
    año=...              -> fuerza otro año (por ejemplo, el año anterior para las variaciones).
    """
    mask = df["Region"].isin(f["regiones"]) & df["Category"].isin(f["categorias"])

    if usar_año:
        mask &= df["Año"] == (año if año is not None else f["año"])

    if usar_descuento:
        if f["descuento"] == "Hasta 20 %":
            mask &= ~df["Descuento_Alto"]
        elif f["descuento"] == "Mayor a 20 %":
            mask &= df["Descuento_Alto"]

    return df[mask]
