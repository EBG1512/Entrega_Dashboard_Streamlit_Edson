"""
data_loader.py
--------------
Carga y preparación de los datos del dashboard (el "back").

Aquí se concentra todo lo que tiene que ver con los datos:
  1. Leer el archivo CSV una sola vez (con @st.cache_data).
  2. Crear las columnas auxiliares que usan las gráficas.
  3. Funciones de cálculo reutilizables (KPIs y agregaciones).
  4. Funciones de formato de números (USD y porcentajes).
"""

from pathlib import Path

import pandas as pd
import streamlit as st

# ------------------------------------------------------------------
# Parámetros de negocio (se cambian aquí y aplican a todo el dashboard)
# ------------------------------------------------------------------
RUTA_DATOS = Path(__file__).resolve().parent.parent / "data" / "Superstore.csv"
META_MARGEN = 0.15        # Meta de margen de ganancia definida para el negocio
UMBRAL_DESCUENTO = 0.20   # Descuento a partir del cual se considera "profundo"

ORDEN_BANDAS = ["Sin descuento", "Hasta 20 %", "21 – 40 %", "Más de 40 %"]


@st.cache_data
def cargar_datos() -> pd.DataFrame:
    """Lee el CSV de Superstore y agrega las columnas que usa el dashboard.

    @st.cache_data guarda el resultado en memoria: el archivo se lee una sola
    vez y no cada vez que el usuario mueve un filtro o cambia de página.
    """
    # El archivo trae caracteres especiales, por eso se lee en latin-1
    df = pd.read_csv(RUTA_DATOS, encoding="latin-1")

    df["Order Date"] = pd.to_datetime(df["Order Date"], format="%m/%d/%Y")
    df["Ship Date"] = pd.to_datetime(df["Ship Date"], format="%m/%d/%Y")

    df["Año"] = df["Order Date"].dt.year
    df["Mes"] = df["Order Date"].dt.to_period("M").dt.to_timestamp()

    df["Banda_Descuento"] = pd.cut(
        df["Discount"],
        bins=[-0.01, 0, 0.20, 0.40, 1.0],
        labels=ORDEN_BANDAS,
    )
    df["Descuento_Alto"] = df["Discount"] > UMBRAL_DESCUENTO
    return df


# ------------------------------------------------------------------
# Cálculos reutilizables
# ------------------------------------------------------------------
def resumen(df: pd.DataFrame, por) -> pd.DataFrame:
    """Agrupa por una o varias columnas y calcula ventas, ganancia y margen."""
    tabla = (
        df.groupby(por, observed=True)
        .agg(
            Ventas=("Sales", "sum"),
            Ganancia=("Profit", "sum"),
            Descuento_prom=("Discount", "mean"),
            Pedidos=("Order ID", "nunique"),
        )
        .reset_index()
    )
    tabla["Margen"] = tabla["Ganancia"] / tabla["Ventas"]
    return tabla


def calcular_kpis(df: pd.DataFrame) -> dict:
    """KPIs principales del período filtrado."""
    ventas = df["Sales"].sum()
    ganancia = df["Profit"].sum()
    return {
        "ventas": ventas,
        "ganancia": ganancia,
        "margen": ganancia / ventas if ventas else 0.0,
        "pedidos": df["Order ID"].nunique(),
    }


def analisis_descuento(df: pd.DataFrame, umbral: float = UMBRAL_DESCUENTO) -> dict:
    """Mide el efecto de las ventas con descuento mayor al umbral."""
    alto = df[df["Discount"] > umbral]
    ventas_total = df["Sales"].sum()
    ganancia_total = df["Profit"].sum()
    ganancia_alto = alto["Profit"].sum()
    return {
        "pct_ventas": alto["Sales"].sum() / ventas_total if ventas_total else 0.0,
        "ganancia_alto": ganancia_alto,
        # Margen si esas ventas hubieran quedado al menos en punto de equilibrio
        "margen_potencial": (ganancia_total - min(ganancia_alto, 0)) / ventas_total if ventas_total else 0.0,
    }


# ------------------------------------------------------------------
# Formato de números
# ------------------------------------------------------------------
def usd(valor: float) -> str:
    """12345.6 -> 'USD 12,3 K' (formato corto en miles)."""
    signo = "−" if valor < 0 else ""
    return f"{signo}USD {abs(valor) / 1000:,.1f} K".replace(",", "X").replace(".", ",").replace("X", ".")


def pct(valor: float, decimales: int = 1) -> str:
    """0.127 -> '12,7 %'."""
    return f"{valor * 100:.{decimales}f} %".replace(".", ",")


def usd_corto(valor: float) -> str:
    """733212 -> '$733 K' (para tarjetas KPI angostas)."""
    signo = "-" if valor < 0 else ""
    return f"{signo}${abs(valor) / 1000:,.0f} K"
