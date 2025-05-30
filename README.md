# Infraes BigData – Captura Automática de Datos del Índice de Shanghái (000001.SS)

Este repositorio contiene un **script Python** (`collector.py`) que automatiza la descarga y el procesamiento de los datos históricos de precios y volúmenes del índice de Shanghái (símbolo `000001.SS`) desde Yahoo Finance, un **módulo de enriquecimiento** que agrega seis KPI financieros, un **módulo de modelado** que entrena y valida un modelo predictivo, y un **panel de control** (`dashboard.py`) que visualiza interactivamente los datos y resultados.

---

##  Descripción del Proyecto

- **Origen de datos**  
  Historial diario de apertura, máximo, mínimo, cierre y volumen en:  
  `https://es.finance.yahoo.com/quote/000001.SS/history/`  
  (periodo 9 de mayo 2024 – 9 de mayo 2025).

- **Componentes principales**  
  1. **`collector.py`**  
     - Selenium (headless) para cargar la página y aceptar cookies.  
     - BeautifulSoup para extraer la tabla HTML.  
     - Normalización de nombres de columna (ASCII, sin símbolos, guiones bajos).  
     - Conversión de fechas en español a ISO (YYYY-MM-DD) y tipado numérico (`float`/`int`).  
     - Almacenamiento incremental en SQLite (`historical.db`), aplicando delta (solo registros nuevos).  
     - Exportación completa a CSV (`historical.csv`).

  2. **`enricher.py`** *(o función integrada en `collector.py`)*  
     Añade las siguientes columnas KPI al dataset:  
     - **Retorno**: cambio porcentual diario sobre cierre anterior.  
     - **Volatilidad_30d**: desviación estándar anualizada de retornos en ventana de 30 días.  
     - **SMA_50d**: media simple de cierres de los últimos 50 días.  
     - **Volumen_20d_avg**: volumen medio de los últimos 20 días.  
     - **Volume_Ratio**: ratio entre el volumen del día y su media a 20 días.  
     - **Drawdown**: caída porcentual desde el máximo histórico acumulado.

  3. **`modeller.py`**  
     - Entrena un modelo de regresión lineal para predecir el cierre del día siguiente.  
     - Evalúa MAE, RMSE y R² y compara contra un predictor ingenuo (persistencia).  
     - Serializa el artefacto en `static/models/model.pkl`.

  4. **`dashboard.py`**  
     - Carga los datos enriquecidos y el modelo serializado.  
     - Genera gráficos interactivos (precios históricos, KPI, predicciones vs realidad).  
     - Despliega un tablero en local o servidor web ligero para seguimiento en tiempo real.

- **GitHub Actions**  
  Workflow `update_data.yml` que, en cada push a `main`:  
  1. Configura Python 3.11 y entorno virtual en Windows.  
  2. Instala dependencias (`pip install -e .`).  
  3. Ejecuta `collector.py` → actualiza DB y CSV.  
  4. Ejecuta `modeller.py` → reentrena y valida el modelo.  
  5. Ejecuta `dashboard.py` → genera/actualiza el tablero de visualización.  
  6. Hace commit y push de `historical.db`, `historical.csv`, `model.pkl` y cualquier configuración del dashboard.

---

## Instalación y Uso Local

```bash
git clone https://github.com/tu-usuario/Infraes_bigdata.git
cd Infraes_bigdata

# 1. Crear y activar entorno virtual (Windows)
python -m venv venv
call venv\Scripts\activate

# 2. Actualizar pip e instalar dependencias
python -m pip install --upgrade pip
pip install -e .

# 3. Ejecutar captura y enriquecimiento
python src\SSE_Composite\collector.py

# 4. Entrenar / validar modelo
python src\SSE_Composite\modeller.py

# 5. Levantar tablero de visualización
python src\SSE_Composite\dashboard.py


Al finalizar, encontrarás los artefactos en:

Base de datos SQLite:
src/SSE_Composite/static/data/historical.db

CSV completo:
src/SSE_Composite/static/data/historical.csv

Modelo serializado:
src/SSE_Composite/static/models/model.pkl

Tablero:
Se levantará localmente mostrando gráficos de precios, KPI y predicciones.
