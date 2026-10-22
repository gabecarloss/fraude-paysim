"""Lê o CSV bruto do PaySim, filtra TRANSFER/CASH_OUT e salva só as colunas usadas.

Uso: python -m src.prepare_data
"""

import pandas as pd

from src.config import FEATURES, PROCESSED_FILE, RAW_CSV, TARGET, TIPOS_USADOS


def main():
    if not RAW_CSV.exists():
        raise FileNotFoundError(
            f"Base não encontrada em {RAW_CSV}. Baixe em "
            "https://www.kaggle.com/datasets/ealaxi/paysim1 e coloque o CSV em data/raw/."
        )

    df = pd.read_csv(RAW_CSV, usecols=["step", "type", "amount", TARGET])
    df = df[df["type"].isin(TIPOS_USADOS)].copy()

    # step é a hora simulada (1 a 744); a hora do dia é o resto da divisão por 24
    df["hour"] = df["step"] % 24

    df = df[["step"] + FEATURES + [TARGET]]
    PROCESSED_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(PROCESSED_FILE, index=False)

    print(f"{len(df):,} transações salvas em {PROCESSED_FILE}")
    print(df[TARGET].value_counts().rename({0: "legítima", 1: "fraude"}))


if __name__ == "__main__":
    main()
