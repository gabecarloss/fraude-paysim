"""Caminhos e constantes compartilhados pelo projeto."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"
REPORTS_DIR = ROOT / "reports"

# Nome do CSV baixado do Kaggle (ealaxi/paysim1)
RAW_CSV = DATA_RAW / "PS_20174392719_1491204439457_log.csv"
PROCESSED_FILE = DATA_PROCESSED / "transacoes.parquet"

# Fraudes só ocorrem nesses dois tipos
TIPOS_USADOS = ["TRANSFER", "CASH_OUT"]

# Entradas do modelo: tipo, valor e hora do dia.
# Saldos ficam de fora (vazam o rótulo) e IDs de conta também.
FEATURES_CATEGORICAS = ["type"]
FEATURES_NUMERICAS = ["amount", "hour"]
FEATURES = FEATURES_CATEGORICAS + FEATURES_NUMERICAS
TARGET = "isFraud"

RANDOM_STATE = 42
TEST_SIZE = 0.2

# Divisão temporal: treino com step <= este valor, teste com o restante.
# step vai de 1 a 744 (horas). Revisar após a análise exploratória.
TEMPORAL_SPLIT_STEP = 24 * 23
