# Infraes BigData – Captura Automática de Datos del Índice de Shanghái (000001.SS)

Este repositorio contiene un **script Python** (`collector.py`) que automatiza la descarga y el procesamiento de los datos históricos de precios y volúmenes del índice de Shanghái (símbolo `000001.SS`) desde Yahoo Finance, así como un **pipeline de GitHub Actions** para ejecutar y versionar automáticamente los resultados.

---

## 📋 Descripción del Script

- **Origen de datos**:  
  `https://es.finance.yahoo.com/quote/000001.SS/history/` (periodo 9 de mayo 2024 – 9 de mayo 2025).

- **Tecnologías**:  
  - Selenium (modo headless) para cargar la página y aceptar cookies.  
  - BeautifulSoup para parsear la tabla HTML.  
  - Pandas para limpiar y tipar columnas (fechas ISO, precios como `float`, volúmenes como `int`).  
  - SQLite para almacenamiento incremental y generación de un CSV completo.

- **Flujo principal**:  
  1. Abrir la página en un navegador controlado por Selenium y pulsar “Aceptar cookies”.  
  2. Esperar a que se cargue la tabla de histórico y extraerla con BeautifulSoup.  
  3. Normalizar nombres de columnas (ASCII sin símbolos, guiones bajos).  
  4. Convertir fechas en español a formato ISO y tipar numéricos.  
  5. Conectar a `historical.db`, leer las fechas ya almacenadas y **añadir solo las filas nuevas**.  
  6. Volcar la serie completa a `historical.csv`.

---

## ⚙️ Instalación y Uso Local

1. Clona el repositorio:
   ```bash
   git clone https://github.com/tu-usuario/Infraes_bigdata.git
   cd Infraes_bigdata
2. Crea y activa un entorno virtual (Windows):
   python -m venv venv
   call venv\Scripts\activate
3. Instala dependencias:
   pip install -e .
4. Ejecuta el script:
   python src\SSE_Composite\collector.py
Los resultados quedan en:
src/SSE_Composite/static/data/historical.db
src/SSE_Composite/static/data/historical.csv


