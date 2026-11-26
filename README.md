# Dashboard de rentabilidad comercial – Superstore

Implementación en **Streamlit + Python** del boceto de la Actividad 2 (Analítica de Datos – Maestría en Ingeniería, IUE).

**Pregunta central:** ¿Estamos creciendo con rentabilidad?
**Usuario:** Director Comercial Nacional (revisión mensual).

## Estructura

```
superstore_dashboard/
├── dash_superstore.py          # Página principal: la historia en 4 actos (boceto)
├── requirements.txt            # Librerías necesarias
├── data/
│   └── Superstore.csv          # Dataset Sales Superstore
├── pages/
│   ├── 1_Diagnostico.py        # ¿Dónde se pierde margen? (regiones y subcategorías)
│   ├── 2_Descuentos.py         # Efecto de los descuentos (umbral ajustable)
│   ├── 3_Detalle_por_Estado.py # Drill-down: productos que pierden en cada estado
│   └── 4_Comparar_Periodos.py  # Qué mejoró y qué empeoró entre dos períodos
└── utils/
    ├── data_loader.py          # Carga de datos (cache), KPIs y formatos
    ├── filters.py              # Filtros de la barra lateral
    └── plots.py                # Gráficas Plotly
```

## Ejecutar en el computador (local)

Requisitos: Python 3.10 o superior.

**Windows (PowerShell o CMD)**

```bash
cd ruta\a\superstore_dashboard
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run dash_superstore.py
```

**macOS / Linux**

```bash
cd ruta/a/superstore_dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run dash_superstore.py
```

El navegador se abre en `http://localhost:8501`. Para detener el servidor: `Ctrl + C` en la terminal.

## Publicar (GitHub + Streamlit Community Cloud)

```bash
git init
git add .
git commit -m "Primer commit: dashboard Superstore"
git branch -M main
git remote add origin https://github.com/USUARIO/superstore-dashboard.git
git push -u origin main
```

Luego, en https://share.streamlit.io: iniciar sesión con GitHub → **Create app** → elegir el repositorio, la rama `main` y el archivo principal `dash_superstore.py` → **Deploy**.

Para actualizar después de un cambio: `git add .` → `git commit -m "mensaje"` → `git push`.
