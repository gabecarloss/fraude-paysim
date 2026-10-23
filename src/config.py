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

# Divisão temporal: treino com step <= este valor (dias 1 a 23), teste com o restante (dias 24 a 31).
# Decisão do grupo após a análise exploratória: manter o corte. As legítimas caem muito a partir
# do dia 18, então o teste tem ~2,6% de fraude e o treino ~0,23% (registrado como limitação).
TEMPORAL_SPLIT_STEP = 24 * 23

# Validação: parte do TREINO separada para escolher o limite de decisão (Etapa 2) sem tocar no teste.
# Estratificada: 20% do treino, mantendo a proporção de fraude.
VALIDATION_SIZE = 0.2
# Temporal: os últimos dias do treino. Ajuste com step <= este valor (dias 1 a 19),
# validação nos dias 20 a 23 (60.569 transações, 980 fraudes).
VALIDATION_TEMPORAL_STEP = 24 * 19
