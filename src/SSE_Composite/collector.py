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
from enricher import enrich_kpis


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
            # aceptar cookies
            try:
                WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.NAME, "agree"))
                ).click()
                self.logger.info("Cookies aceptadas.")
            except:
                self.logger.info("No se encontró botón de cookies.")
            # esperar tabla
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, '//table'))
            )
            soup = BeautifulSoup(driver.page_source, 'html.parser')
            table = soup.find('table')
            if not table:
                raise Exception("Tabla no encontrada")
            self.logger.info("Tabla encontrada correctamente.")
            return table
        finally:
            driver.quit()

    def clean_header(self, th):
        for tag in th.find_all(['span', 'svg', 'div']):
            tag.decompose()
        text = th.get_text(separator=' ', strip=True)
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\s+', '_', text)
        return text.strip()

    def parse_table(self, table):
        headers = [self.clean_header(th) for th in table.find('thead').find_all('th')]
        rows = []
        for tr in table.find('tbody').find_all('tr'):
            cols = [td.get_text(strip=True) for td in tr.find_all('td')]
            if len(cols) == len(headers):
                rows.append(cols)
        df = pd.DataFrame(rows, columns=headers)
        # normalizar fechas
        meses = {'ene':'01','feb':'02','mar':'03','abr':'04','may':'05','jun':'06',
                 'jul':'07','ago':'08','sept':'09','oct':'10','nov':'11','dic':'12'}
        if 'Fecha' in df.columns:
            norm = []
            for f in df['Fecha']:
                p = f.lower().split()
                if len(p)==3 and p[1] in meses:
                    norm.append(f"{p[2]}-{meses[p[1]]}-{p[0].zfill(2)}")
                else:
                    norm.append(None)
            df['Fecha'] = pd.to_datetime(norm, errors='coerce')
        # convertir a numérico
        for col in df.columns:
            if col == 'Fecha':
                continue
            if col.lower() == 'volumen':
                df[col] = df[col].str.replace('.', '', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce', downcast='integer')
            else:
                df[col] = df[col].str.replace('.', '', regex=False).str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors='coerce')
        self.logger.info(f"{len(df)} filas procesadas.")
        return df

    def save_to_sqlite(self, df, table='historical_prices'):
        # asegurar carpeta
        dirp = os.path.dirname(self.db_path)
        if dirp and not os.path.exists(dirp):
            os.makedirs(dirp, exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        # cargar históricos
        try:
            old = pd.read_sql(f"SELECT * FROM {table}", conn, parse_dates=['Fecha'])
            self.logger.info(f"{len(old)} registros existentes.")
        except Exception:
            old = pd.DataFrame(columns=df.columns)
            self.logger.info("No hay tabla previa.")

        # quedarnos sólo con las filas nuevas (deltas)
        new_rows = df.loc[~df['Fecha'].isin(old['Fecha'])]
        if new_rows.empty:
            self.logger.info("No hay registros nuevos para insertar en SQLite.")
            conn.close()
            return

        # para calcular correctamente los KPIs, juntamos histórico + nuevos
        temp = pd.concat([old, new_rows]).sort_values('Fecha').reset_index(drop=True)
        enriched_full = enrich_kpis(temp, logger=self.logger)

        # extraemos sólo las filas nuevas ya enriquecidas
        enriched_new = enriched_full.loc[enriched_full['Fecha'].isin(new_rows['Fecha'])]

        # inserción incremental
        enriched_new.to_sql(table, conn, if_exists='append', index=False)
        conn.close()
        self.logger.info(f"Insertados {len(enriched_new)} registros nuevos en '{table}'.")

    def save_to_csv(self, df):
        dirp = os.path.dirname(self.csv_path)
        if dirp and not os.path.exists(dirp):
            os.makedirs(dirp, exist_ok=True)

        if os.path.exists(self.csv_path):
            old_csv = pd.read_csv(self.csv_path, parse_dates=['Fecha'])
            new_csv = df.loc[~df['Fecha'].isin(old_csv['Fecha'])]
            if new_csv.empty:
                self.logger.info("No hay registros nuevos para CSV.")
                return
            new_csv.to_csv(self.csv_path, mode='a', index=False, header=False)
            self.logger.info(f"CSV: añadidos {len(new_csv)} registros nuevos.")
        else:
            df.to_csv(self.csv_path, index=False)
            self.logger.info(f"CSV creado: {self.csv_path}")

    def run(self):
        try:
            table = self.fetch_data()
            df = self.parse_table(table)
            # enriquecemos el batch recién extraído para CSV si se desea
            df = enrich_kpis(df, logger=self.logger)
            self.save_to_sqlite(df)
            self.save_to_csv(df)
            self.logger.info('Proceso completado.')
        except Exception as e:
            self.logger.exception(f"Error: {e}")


if __name__ == '__main__':
    Collector().run()