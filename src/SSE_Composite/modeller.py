import os
import sqlite3
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib

MODEL_DIR = os.path.join('src', 'SSE_Composite', 'static', 'models')
MODEL_PATH = os.path.join(MODEL_DIR, 'model.pkl')
DB_PATH = os.path.join('src', 'SSE_Composite', 'static', 'data', 'historical.db')

class Modeller:
    def __init__(self):
        self.db_path = DB_PATH
        self.model_path = MODEL_PATH

    def train(self):
        """
        Entrena un modelo de regresión para predecir el precio de cierre del siguiente día.
        Compara contra un predictor ingenuo (persistencia) y reporta MAE, RMSE y R².
        Guarda el artefacto en static/models/model.pkl.
        """
        os.makedirs(MODEL_DIR, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        info = pd.read_sql("PRAGMA table_info(historical_prices)", conn)
        close_col = next(c for c in info['name'] if c.lower().startswith('cerr'))
        df = pd.read_sql(
            f"SELECT Fecha, \"{close_col}\" AS Close FROM historical_prices ORDER BY Fecha", 
            conn, parse_dates=['Fecha']
        )
        conn.close()

        # Preparar variables
        df['Next_Close'] = df['Close'].shift(-1)
        df = df.dropna().reset_index(drop=True)
        X = df[['Close']].values
        y = df['Next_Close'].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        # Modelo de regresión lineal
        model = LinearRegression()
        model.fit(X_train, y_train)
        preds = model.predict(X_test)

        # Métricas del modelo
        mae = mean_absolute_error(y_test, preds)
        mse = mean_squared_error(y_test, preds)
        rmse = mse ** 0.5
        r2 = r2_score(y_test, preds)

        # Predictor ingenuo (persistencia: predice cierre de hoy como mañana)
        naive_preds = X_test.flatten()
        mae_naive = mean_absolute_error(y_test, naive_preds)
        mse_naive = mean_squared_error(y_test, naive_preds)
        rmse_naive = mse_naive ** 0.5
        r2_naive = r2_score(y_test, naive_preds)

        print("=== Evaluación del modelo ===")
        print(f"MAE modelo:  {mae:.4f}")
        print(f"RMSE modelo: {rmse:.4f}")
        print(f"R2 modelo:   {r2:.4f}\n")
        print("=== Predictor ingenuo ===")
        print(f"MAE naive:  {mae_naive:.4f}")
        print(f"RMSE naive: {rmse_naive:.4f}")
        print(f"R2 naive:   {r2_naive:.4f}\n")

        # Guardar modelo entrenado
        joblib.dump(model, self.model_path)
        print(f"Modelo guardado en {self.model_path}")

    def predict(self, X_new):
        """
        Carga el modelo guardado y retorna predicciones para X_new.
        X_new debe tener la misma estructura de la fase de entrenamiento.
        """
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"No se encontró el modelo en {self.model_path}")
        model = joblib.load(self.model_path)
        return model.predict(X_new)

if __name__ == '__main__':
    m = Modeller()
    m.train()
    # Ejemplo de predicción con los últimos cierres
    conn = sqlite3.connect(DB_PATH)
    info = pd.read_sql("PRAGMA table_info(historical_prices)", conn)
    close_col = next(c for c in info['name'] if c.lower().startswith('cerr'))
    df_full = pd.read_sql(
        f"SELECT \"{close_col}\" AS Close FROM historical_prices ORDER BY Fecha", 
        conn
    )
    conn.close()
    X_last = df_full[['Close']].tail(5).values
    print("Predicciones:", m.predict(X_last))





