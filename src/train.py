"""Treina Random Forest e Regressão Logística e salva os modelos em models/.

Uso: python -m src.train

São 8 modelos: 2 algoritmos (RF e LR) x 2 formas de tratar o desbalanceamento
(class_weight e SMOTE) x 2 divisões dos dados (estratificada e temporal).
Cada modelo é um Pipeline completo (pré-processamento + SMOTE, se houver + classificador),
salvo com joblib em models/<modelo>_<balanceamento>_<divisao>.joblib.
"""

import time

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import (
    FEATURES,
    FEATURES_CATEGORICAS,
    FEATURES_NUMERICAS,
    MODELS_DIR,
    PROCESSED_FILE,
    RANDOM_STATE,
    REPORTS_DIR,
    TARGET,
    TEMPORAL_SPLIT_STEP,
    TEST_SIZE,
    VALIDATION_SIZE,
    VALIDATION_TEMPORAL_STEP,
)

DIVISOES = ["estratificada", "temporal"]
MODELOS = ["rf", "lr"]
BALANCEAMENTOS = ["classweight", "smote"]


def carregar_dados():
    return pd.read_parquet(PROCESSED_FILE)


def dividir(df, divisao):
    """Separa a base em (treino, validacao, teste).

    O teste é separado primeiro e não é usado em nenhum ajuste. A validação sai do treino e
    serve para escolher o limite de decisão na avaliação. A função é determinística: chamada
    de novo (por exemplo, em src/evaluate.py), devolve exatamente os mesmos conjuntos.
    """
    if divisao == "estratificada":
        # stratify mantém a mesma proporção de fraude (0,296%) em todos os conjuntos
        treino, teste = train_test_split(
            df, test_size=TEST_SIZE, stratify=df[TARGET], random_state=RANDOM_STATE
        )
        treino, validacao = train_test_split(
            treino, test_size=VALIDATION_SIZE, stratify=treino[TARGET], random_state=RANDOM_STATE
        )
    elif divisao == "temporal":
        # o modelo aprende com o passado e é testado no futuro, como seria na prática
        teste = df[df["step"] > TEMPORAL_SPLIT_STEP]
        validacao = df[(df["step"] > VALIDATION_TEMPORAL_STEP) & (df["step"] <= TEMPORAL_SPLIT_STEP)]
        treino = df[df["step"] <= VALIDATION_TEMPORAL_STEP]
    else:
        raise ValueError(f"Divisão desconhecida: {divisao}")
    return treino, validacao, teste


def montar_pipeline(modelo, balanceamento):
    """Monta o Pipeline: pré-processamento -> (SMOTE) -> classificador."""
    # type vira duas colunas 0/1 (TRANSFER, CASH_OUT); amount e hour ficam com média 0 e desvio 1.
    # A escala importa para a LR e para o SMOTE (que mede distância entre transações):
    # sem ela, amount (milhões) dominaria hour (0 a 23).
    preprocessamento = ColumnTransformer([
        ("categoricas", OneHotEncoder(handle_unknown="ignore"), FEATURES_CATEGORICAS),
        ("numericas", StandardScaler(), FEATURES_NUMERICAS),
    ])

    # Com SMOTE o treino já fica equilibrado (1 fraude para 1 legítima), então não usamos
    # class_weight junto, para não corrigir o desbalanceamento duas vezes.
    peso = "balanced" if balanceamento == "classweight" else None

    if modelo == "rf":
        # 100 árvores (padrão); cada folha precisa de pelo menos 50 transações, para não decorar
        # casos isolados e para as árvores não ficarem enormes; n_jobs=-1 usa todos os núcleos.
        classificador = RandomForestClassifier(
            n_estimators=100, min_samples_leaf=50, class_weight=peso,
            n_jobs=-1, random_state=RANDOM_STATE,
        )
    elif modelo == "lr":
        # parâmetros padrão; max_iter maior só para garantir que o ajuste converge
        classificador = LogisticRegression(class_weight=peso, max_iter=1000)
    else:
        raise ValueError(f"Modelo desconhecido: {modelo}")

    etapas = [("preprocessamento", preprocessamento)]
    if balanceamento == "smote":
        # dentro do Pipeline, o SMOTE só age no fit (treino); no predict ele é ignorado
        etapas.append(("smote", SMOTE(random_state=RANDOM_STATE)))
    etapas.append(("classificador", classificador))
    return Pipeline(etapas)


def descrever(nome, parte):
    fraudes = int(parte[TARGET].sum())
    print(f"  {nome:<10} {len(parte):>9,} transações  {fraudes:>6,} fraudes  ({fraudes / len(parte):.2%})")


def main():
    df = carregar_dados()
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    tempos = []

    for divisao in DIVISOES:
        treino, validacao, teste = dividir(df, divisao)
        print(f"\nDivisão {divisao}:")
        descrever("treino", treino)
        descrever("validação", validacao)
        descrever("teste", teste)

        for modelo in MODELOS:
            for balanceamento in BALANCEAMENTOS:
                nome = f"{modelo}_{balanceamento}_{divisao}"
                pipeline = montar_pipeline(modelo, balanceamento)

                inicio = time.perf_counter()
                pipeline.fit(treino[FEATURES], treino[TARGET])  # só o treino entra no ajuste
                segundos = time.perf_counter() - inicio

                arquivo = MODELS_DIR / f"{nome}.joblib"
                joblib.dump(pipeline, arquivo)
                megabytes = arquivo.stat().st_size / 1e6
                print(f"  {nome:<30} {segundos:>6.0f} s  {megabytes:>7.1f} MB", flush=True)
                tempos.append({
                    "modelo": modelo, "balanceamento": balanceamento, "divisao": divisao,
                    "linhas_treino": len(treino), "segundos": round(segundos, 1),
                    "arquivo_mb": round(megabytes, 1),
                })

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(tempos).to_csv(REPORTS_DIR / "tempos_treino.csv", index=False)
    print(f"\n{len(tempos)} modelos salvos em {MODELS_DIR}")
    print(f"Tempos em {REPORTS_DIR / 'tempos_treino.csv'}")


if __name__ == "__main__":
    main()
