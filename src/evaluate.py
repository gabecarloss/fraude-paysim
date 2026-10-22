"""Avalia os modelos salvos no conjunto de teste.

Uso: python -m src.evaluate

TODO:
- Precision, Recall, F1, matriz de confusão, PR-AUC (average_precision_score) e ROC-AUC
- curva Precision x Recall e escolha do limite de decisão
- importância das variáveis do Random Forest
- salvar tabelas/gráficos em reports/
"""

from src.config import MODELS_DIR


def main():
    raise NotImplementedError(f"Implementar a avaliação dos modelos em {MODELS_DIR}")


if __name__ == "__main__":
    main()
