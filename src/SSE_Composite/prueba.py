import os
import re
import pandas as pd
import sqlite3
import unicodedata
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from logger_config import setup_logger


class Collector:
    def __init__(self):
        self.url = "https://es.finance.yahoo.com/quote/000001.SS/history/"
        self.db_path = os.path.join("src", "SSE_Composite", "static", "data", "historical.db")
        self.csv_path = os.path.join("src", "SSE_Composite", "static", "data", "historical.csv")
        self.logger = setup_logger()
        self.logger.info("Inicializando Collector.")

    def fetch_data(self):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        driver = webdriver.Chrome(options=options)

        try:
            driver.get(self.url)
            self.logger.info(f"Abriendo página: {self.url}")

            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "agree"))
                ).click()
                self.logger.info("Cookies aceptadas.")
            except:
                self.logger.info("No se encontró el botón de cookies.")

            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//table'))
            )

            soup = BeautifulSoup(driver.page_source, "html.parser")
            table = soup.find("table")
            if not table:
                raise Exception("Tabla no encontrada.")
            self.logger.info("Tabla encontrada correctamente.")
            return table
        finally:
            driver.quit()

    def clean_header(self, th):
        for tag in th.find_all(["span", "svg", "div"]):
            tag.decompose()
        text = th.get_text(separator=" ", strip=True)
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^\w\s]", "", text)
        text = re.sub(r"\s+", "_", text)
        return text.strip()

    def parse_table(self, table):
        headers = [self.clean_header(th) for th in table.find("thead").find_all("th")]
        rows = []
        for tr in table.find("tbody").find_all("tr"):
            cols = [td.get_text(strip=True) for td in tr.find_all("td")]
            if len(cols) == len(headers):
                rows.append(cols)

        df = pd.DataFrame(rows, columns=headers)

        # Mapear meses español → número
        meses_es = {
            "ene": "01", "feb": "02", "mar": "03", "abr": "04", "may": "05", "jun": "06",
            "jul": "07", "ago": "08", "sept": "09", "oct": "10", "nov": "11", "dic": "12"
        }
        if "Fecha" in df.columns:
            norm_dates = []
            for fecha in df["Fecha"]:
                partes = fecha.lower().split()
                if len(partes) == 3 and partes[1] in meses_es:
                    # YYYY-MM-DD
                    norm_dates.append(f"{partes[2]}-{meses_es[partes[1]]}-{partes[0].zfill(2)}")
                else:
                    norm_dates.append(None)
            df["Fecha"] = pd.to_datetime(norm_dates, errors="coerce")

        # Convertir numéricos
        for col in df.columns:
            if col == "Fecha":
                continue
            if col.lower() == "volumen":
                df[col] = df[col].str.replace(".", "", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce", downcast="integer")
            else:
                df[col] = df[col].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce", downcast="float")

        self.logger.info(f"{len(df)} filas procesadas.")
        return df

    def save_to_sqlite(self, df, table_name="historical_prices"):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)

        # Leer fechas ya almacenadas
        try:
            existing = pd.read_sql(f"SELECT Fecha FROM {table_name}", conn)
            existing_dates = pd.to_datetime(existing["Fecha"]).dt.date
            self.logger.info(f"{len(existing_dates)} fechas existentes detectadas.")
        except Exception:
            existing_dates = pd.Series([], dtype="object")
            self.logger.info("Tabla no existe o vacía; se crearán registros nuevos.")

        # Filtrar delta
        df["Fecha_date"] = df["Fecha"].dt.date
        df_new = df[~df["Fecha_date"].isin(existing_dates)].copy()
        df_new.drop(columns=["Fecha_date"], inplace=True)

        if df_new.empty:
            self.logger.info("No hay registros nuevos para insertar.")
        else:
            df_new.to_sql(table_name, conn, if_exists="append", index=False)
            self.logger.info(f"{len(df_new)} nuevos registros insertados.")

        conn.close()

    def save_to_csv(self, df):
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
        df.to_csv(self.csv_path, index=False)
        self.logger.info(f"Datos guardados en CSV: {self.csv_path}")

    def run(self):
        try:
            table = self.fetch_data()
            df = self.parse_table(table)
            self.save_to_sqlite(df)
            self.save_to_csv(df)
            self.logger.info("Proceso completado exitosamente.")
        except Exception as e:
            self.logger.exception(f"Falló la ejecución: {str(e)}")


if __name__ == "__main__":
    Collector().run()

