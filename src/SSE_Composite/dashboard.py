# src/SSE_Composite/dashboard.py

import os
import sys
import argparse
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# AÑADIMOS la carpeta actual al sys.path para importar enricher.py
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from enricher import enrich_kpis

DB_PATH    = os.path.join(BASE_DIR, 'static', 'data', 'historical.db')
ART_DIR    = os.path.join(BASE_DIR, 'artifacts')
HTML_REPORT = os.path.join(ART_DIR, 'report.html')
os.makedirs(ART_DIR, exist_ok=True)


def load_data():
    """Carga el DataFrame desde SQLite o lanza FileNotFoundError."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"BD no encontrada: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM historical_prices", conn, parse_dates=['Fecha'])
    conn.close()
    return df


def export_report():
    """Genera PNGs y un HTML estático con KPIs y gráficos."""
    df = load_data()
    df = enrich_kpis(df)
    fecha_max = df['Fecha'].max()
    latest = df[df['Fecha'] == fecha_max].iloc[0]

    # 1) Cabecera HTML con métricas
    with open(HTML_REPORT, 'w', encoding='utf-8') as f:
        f.write(f"<html><head><meta charset='utf-8'><title>Reporte KPIs SSE Composite</title></head><body>\n")
        f.write(f"<h1>KPIs al {fecha_max.date()}</h1>\n<ul>\n")
        for k in ["Retorno", "Volatilidad_30d", "SMA_50d", "Volumen_20d_avg", "Volume_Ratio"]:
            f.write(f"<li><strong>{k}:</strong> {latest[k]:.4f}</li>\n")
        f.write("</ul><hr>\n")

    # 2) Gráficos individuales
    for k in ["Retorno", "Volatilidad_30d", "SMA_50d", "Volumen_20d_avg", "Volume_Ratio"]:
        fig, ax = plt.subplots()
        ax.plot(df['Fecha'], df[k])
        ax.set_title(k)
        ax.set_xlabel('Fecha')
        ax.set_ylabel(k)
        fig.tight_layout()

        png_path = os.path.join(ART_DIR, f"{k}.png")
        fig.savefig(png_path)
        plt.close(fig)

        # Append al HTML
        with open(HTML_REPORT, 'a', encoding='utf-8') as f:
            f.write(f"<h2>{k}</h2>\n")
            f.write(f"<img src='{os.path.basename(png_path)}' style='max-width:800px;width:100%;'>\n")

    with open(HTML_REPORT, 'a', encoding='utf-8') as f:
        f.write("</body></html>")

    print(f"✅ Reporte estático generado en {ART_DIR}")


def render_dashboard():
    """Arranca la app Streamlit."""
    import streamlit as st  # solo aquí importamos Streamlit
    st.set_page_config(page_title="KPIs SSE Composite", layout="wide")
    st.title("📊 Dashboard de KPIs SSE Composite")

    try:
        df = load_data()
    except Exception as e:
        st.error(f"❌ {e}")
        return

    df = enrich_kpis(df)
    fecha_max = df['Fecha'].max()
    latest = df[df['Fecha'] == fecha_max].iloc[0]

    st.subheader(f"KPIs al {fecha_max.date()}")
    kpis = {
        "Retorno": latest['Retorno'],
        "Volatilidad 30d": latest['Volatilidad_30d'],
        "SMA 50d": latest['SMA_50d'],
        "Volumen Prom. 20d": latest['Volumen_20d_avg'],
        "Volume Ratio": latest['Volume_Ratio']
    }
    cols = st.columns(len(kpis))
    for col, (label, val) in zip(cols, kpis.items()):
        col.metric(label, f"{val:.4f}")

    st.markdown("---")
    st.subheader("Evolución Histórica de KPIs")

    kpi_cols = list(kpis.keys())
    # Primera fila: 3 gráficos
    row1 = st.columns(3)
    for i, name in enumerate(kpi_cols[:3]):
        with row1[i]:
            st.markdown(f"**{name}**")
            st.line_chart(df.set_index('Fecha')[[name]], height=250)

    # Segunda fila: 2 gráficos
    row2 = st.columns(2)
    for i, name in enumerate(kpi_cols[3:]):
        with row2[i]:
            st.markdown(f"**{name}**")
            st.line_chart(df.set_index('Fecha')[[name]], height=250)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', action='store_true',
                        help="Genera artifacts (PNG + report.html) y sale")
    args = parser.parse_args()

    if args.export:
        export_report()
    else:
        # Modo interactivo Streamlit
        render_dashboard()


