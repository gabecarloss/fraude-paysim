"""Treina Random Forest e Regressão Logística e salva os modelos em models/.

Uso: python -m src.train

TODO:
- dividir treino/teste (estratificado e temporal, ver config.TEMPORAL_SPLIT_STEP)
- pré-processamento: OneHotEncoder em "type", StandardScaler em amount/hour (para a LR)
- variantes de desbalanceamento, sempre dentro de imblearn.pipeline.Pipeline:
    * class_weight="balanced"
    * SMOTE (aplicado só no fit, nunca no teste)
- salvar cada pipeline com joblib.dump em config.MODELS_DIR
"""

from src.config import PROCESSED_FILE


def main():
    raise NotImplementedError(f"Implementar o treinamento a partir de {PROCESSED_FILE}")


if __name__ == "__main__":
    main()
