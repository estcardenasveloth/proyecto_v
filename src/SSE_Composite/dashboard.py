import os
import sys
import argparse
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
from enricher import enrich_kpis

DB_PATH    = os.path.join(BASE_DIR, 'static', 'data', 'historical.db')
ART_DIR    = os.path.join(BASE_DIR, 'artifacts')
HTML_REPORT = os.path.join(ART_DIR, 'report.html')
os.makedirs(ART_DIR, exist_ok=True)


def load_data():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"BD no encontrada: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM historical_prices", conn, parse_dates=['Fecha'])
    conn.close()
    return df


def export_report():
    df = load_data()
    df = enrich_kpis(df)
    fecha_max = df['Fecha'].max()
    latest = df[df['Fecha'] == fecha_max].iloc[0]

    with open(HTML_REPORT, 'w', encoding='utf-8') as f:
        f.write(f"<html><head><meta charset='utf-8'><title>Reporte KPIs SSE Composite</title></head><body>\n")
        f.write(f"<h1>KPIs al {fecha_max.date()}</h1>\n<ul>\n")
        for k in ["Retorno", "Volatilidad_30d", "SMA_50d", "Volumen_20d_avg", "Volume_Ratio", "EMA_20d"]:
            f.write(f"<li><strong>{k}:</strong> {latest[k]:.4f}</li>\n")
        f.write("</ul><hr>\n")

    for k in ["Retorno", "Volatilidad_30d", "SMA_50d", "Volumen_20d_avg", "Volume_Ratio", "EMA_20d"]:
        fig, ax = plt.subplots()
        ax.plot(df['Fecha'], df[k])
        ax.set_title(k)
        ax.set_xlabel('Fecha')
        ax.set_ylabel(k)
        fig.tight_layout()

        png_path = os.path.join(ART_DIR, f"{k}.png")
        fig.savefig(png_path)
        plt.close(fig)

        with open(HTML_REPORT, 'a', encoding='utf-8') as f:
            f.write(f"<h2>{k}</h2>\n")
            f.write(f"<img src='{os.path.basename(png_path)}' style='max-width:800px;width:100%;'>\n")

    with open(HTML_REPORT, 'a', encoding='utf-8') as f:
        f.write("</body></html>")

    print(f"Reporte estatico generado en {ART_DIR}")


def render_dashboard():
    import streamlit as st
    st.set_page_config(page_title="KPIs SSE Composite", layout="wide")
    st.title("Dashboard de KPIs SSE Composite")

    try:
        df = load_data()
    except Exception as e:
        st.error(f"{e}")
        return

    df = enrich_kpis(df)

    # Sidebar filters
    st.sidebar.header("Filtros")
    min_date, max_date = df['Fecha'].min(), df['Fecha'].max()
    fecha_ini, fecha_fin = st.sidebar.date_input(
        "Rango de fechas",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    df = df[(df['Fecha'] >= pd.to_datetime(fecha_ini)) & (df['Fecha'] <= pd.to_datetime(fecha_fin))]

    señales = sorted(df['Senal_Mercado'].dropna().unique())
    señal_sel = st.sidebar.multiselect("Tipo de señal", options=señales, default=señales)
    df = df[df['Senal_Mercado'].isin(señal_sel)]

    min_dd, max_dd = float(df['Drawdown'].min()), float(df['Drawdown'].max())
    umbral_dd = st.sidebar.slider("Drawdown mínimo", min_value=min_dd, max_value=max_dd, value=min_dd)
    df = df[df['Drawdown'] >= umbral_dd]

    fecha_max = df['Fecha'].max()
    latest = df[df['Fecha'] == fecha_max].iloc[0]

    st.subheader(f"KPIs al {fecha_max.date()}")
    kpi_map = {
        "Retorno": "Retorno",
        "Volatilidad 30d": "Volatilidad_30d",
        "SMA 50d": "SMA_50d",
        "Volumen Prom. 20d": "Volumen_20d_avg",
        "Volume Ratio": "Volume_Ratio",
        "EMA 20d": "EMA_20d"
    }
    kpis = {label: latest[col] for label, col in kpi_map.items()}
    cols = st.columns(len(kpis))
    for col, (label, val) in zip(cols, kpis.items()):
        col.metric(label, f"{val:.4f}")

    st.markdown("---")
    st.subheader("Evolución Histórica de KPIs (filtrada)")

    labels = list(kpi_map.keys())
    cols_names = list(kpi_map.values())
    row1 = st.columns(3)
    for i, (label, col) in enumerate(zip(labels[:3], cols_names[:3])):
        with row1[i]:
            st.markdown(f"**{label}**")
            st.line_chart(df.set_index('Fecha')[[col]], height=250)
    remaining = len(labels) - 3
    row2 = st.columns(remaining)
    for i, (label, col) in enumerate(zip(labels[3:], cols_names[3:])):
        with row2[i]:
            st.markdown(f"**{label}**")
            st.line_chart(df.set_index('Fecha')[[col]], height=250)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', action='store_true', help="Genera artifacts (PNG + report.html) y sale")
    args = parser.parse_args()
    if args.export:
        export_report()
    else:
        render_dashboard()



