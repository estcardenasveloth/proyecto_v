import pandas as pd

def enrich_kpis(df: pd.DataFrame, logger=None) -> pd.DataFrame:
    """
    Calcula y añade KPIs al DataFrame:
      - Retorno diario
      - Volatilidad anualizada (30 días)
      - Media móvil 50 días (SMA_50d)
      - Volumen promedio 20 días (Volumen_20d_avg)
      - Ratio de volumen (Volume_Ratio)
      - Drawdown
      - Señal de mercado (Senal_Mercado)
    """
    # detectar columnas dinámicamente
    close_col = next(c for c in df.columns if c.lower().startswith('cerr'))
    vol_col   = next(c for c in df.columns if c.lower() == 'volumen')
    df = df.sort_values('Fecha').reset_index(drop=True)

    # Retorno y volatilidad
    df['Retorno'] = df[close_col].pct_change()
    df['Volatilidad_30d'] = df['Retorno'].rolling(30).std() * (252**0.5)

    # Media móvil y volumen promedio
    df['SMA_50d'] = df[close_col].rolling(50).mean()
    df['Volumen_20d_avg'] = df[vol_col].rolling(20).mean()
    df['Volume_Ratio'] = df[vol_col] / df['Volumen_20d_avg']

    # Drawdown
    run_max = df[close_col].cummax()
    df['Drawdown'] = (df[close_col] - run_max) / run_max

    # Señal de mercado
    def classify(row):
        signals = []
        if pd.notna(row['SMA_50d']):
            signals.append('Alcista' if row[close_col] > row['SMA_50d'] else 'Bajista')
        if pd.notna(row['Volatilidad_30d']):
            signals.append('Alta volatilidad' if row['Volatilidad_30d'] > 0.3 else 'Baja volatilidad')
        if pd.notna(row['Volume_Ratio']):
            signals.append('Volumen elevado' if row['Volume_Ratio'] > 1.2 else 'Volumen normal')
        return '; '.join(signals)

    df['Senal_Mercado'] = df.apply(classify, axis=1)

    if logger:
        logger.info('KPIs calculados y señal añadida.')
    return df
