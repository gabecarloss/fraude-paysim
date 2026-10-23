"""Avalia os 8 modelos salvos, escolhe o limite de decisão e o modelo da aplicação.

Uso: python -m src.evaluate

Para cada modelo:
1. o limite de decisão é escolhido na VALIDAÇÃO (maior F1); o teste não participa da escolha;
2. no TESTE são calculadas PR-AUC (métrica principal), ROC-AUC, Precision, Recall, F1 e a
   matriz de confusão, no limite 0,5 e no limite escolhido.

Saídas: reports/metricas.csv, reports/importancia_variaveis.csv, figuras em reports/figures/
e o modelo da aplicação (pipeline + limite) em models/modelo_aplicacao.joblib.
"""

import gc

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)

from src.config import (
    DIVISAO_APLICACAO,
    FEATURES,
    FIGURES_DIR,
    MODELO_APLICACAO,
    MODELS_DIR,
    REPORTS_DIR,
    TARGET,
    TOLERANCIA_PR_AUC,
)
from src.train import BALANCEAMENTOS, DIVISOES, MODELOS, carregar_dados, dividir

# Uma cor fixa por modelo, igual em todos os gráficos (paleta categórica da skill dataviz)
CORES = {
    "rf_classweight": "#2a78d6",
    "rf_smote": "#eb6834",
    "lr_classweight": "#1baf7a",
    "lr_smote": "#eda100",
}
CINZA = "#52514e"


def br(texto):
    """Troca ponto e vírgula para o formato brasileiro: 1,234.5 -> 1.234,5."""
    return texto.translate(str.maketrans(",.", ".,"))


def rotulo(modelo, balanceamento):
    return f"{modelo.upper()} + {'class_weight' if balanceamento == 'classweight' else 'SMOTE'}"


def escolher_limite(y_val, prob_val):
    """Devolve o limite com o maior F1 na validação.

    Abaixar o limite marca mais transações como fraude: pega mais fraudes (Recall sobe), mas gera
    mais alarmes falsos (Precision cai). Subir o limite faz o contrário. O F1 é a média harmônica
    dos dois, então só fica alto quando ambos estão razoáveis.
    """
    precision, recall, limites = precision_recall_curve(y_val, prob_val)
    # o último ponto da curva (precision 1, recall 0) não tem limite associado
    precision, recall = precision[:-1], recall[:-1]
    f1 = 2 * precision * recall / np.maximum(precision + recall, 1e-12)
    return float(limites[np.argmax(f1)])


def metricas(y, prob, limite, sufixo):
    """Precision, Recall, F1 e matriz de confusão com um limite (fraude se prob >= limite)."""
    previsto = (prob >= limite).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, previsto, labels=[0, 1]).ravel()
    return {
        f"precision_{sufixo}": precision_score(y, previsto, zero_division=0),
        f"recall_{sufixo}": recall_score(y, previsto, zero_division=0),
        f"f1_{sufixo}": f1_score(y, previsto, zero_division=0),
        f"tn_{sufixo}": int(tn),
        f"fp_{sufixo}": int(fp),
        f"fn_{sufixo}": int(fn),
        f"tp_{sufixo}": int(tp),
    }


def importancia_por_variavel(pipeline):
    """Soma a importância das colunas transformadas por variável original (type, amount, hour).

    É a importância por impureza (MDI) do Random Forest: quanto cada variável ajudou a separar
    as classes nas árvores. Ela tende a favorecer variáveis contínuas (com muitos pontos de corte),
    então é uma indicação, não uma medida exata.
    """
    # nomes como "categoricas__type_TRANSFER" e "numericas__amount"
    nomes = pipeline.named_steps["preprocessamento"].get_feature_names_out()
    valores = pipeline.named_steps["classificador"].feature_importances_
    return {
        variavel: float(sum(v for n, v in zip(nomes, valores) if n.split("__")[1].startswith(variavel)))
        for variavel in FEATURES
    }


def escolher_melhor(resultados):
    """Maior PR-AUC na validação. Se um arquivo menor ficar a menos de TOLERANCIA_PR_AUC dela, fica o menor.

    Só usa a validação: o teste não influencia a escolha.
    """
    maior = resultados["pr_auc_validacao"].max()
    candidatos = resultados[resultados["pr_auc_validacao"] >= maior - TOLERANCIA_PR_AUC]
    return candidatos.sort_values("arquivo_mb").iloc[0]


def grafico_curvas(resultados, y_teste, prob_teste):
    fig, eixos = plt.subplots(1, 2, figsize=(13, 5))
    for ax, divisao in zip(eixos, DIVISOES):
        parte = resultados[resultados["divisao"] == divisao]
        for _, linha in parte.iterrows():
            chave = f"{linha['modelo']}_{linha['balanceamento']}"
            precision, recall, _ = precision_recall_curve(y_teste[divisao], prob_teste[linha["nome"]])
            ax.plot(recall, precision, color=CORES[chave], linewidth=2,
                    label=f"{rotulo(linha['modelo'], linha['balanceamento'])} "
                          f"(PR-AUC {br(format(linha['pr_auc_teste'], '.3f'))})")
            # ponto em que o modelo opera no teste com o limite escolhido na validação
            ax.plot(linha["recall_limite"], linha["precision_limite"], "o", markersize=8,
                    color=CORES[chave], markeredgecolor="white", markeredgewidth=2)
        fraude = parte["fraude_teste"].iloc[0]
        ax.axhline(fraude, color=CINZA, linestyle="--", linewidth=1,
                   label=f"Palpite aleatório ({br(format(fraude, '.2%'))})")
        ax.set_title(f"Divisão {divisao}: teste com {br(format(fraude, '.2%'))} de fraude")
        ax.set_xlabel("Recall (fração das fraudes encontradas)")
        ax.set_ylabel("Precision (fração dos alertas que eram fraude)")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1.02)
        ax.grid(color="#e5e4e0", linewidth=0.8)
        ax.legend(loc="upper right", fontsize=9)
    fig.suptitle("Curvas Precision x Recall no teste (círculo = limite escolhido na validação)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "curvas_precision_recall.png", dpi=150)
    plt.close(fig)


def grafico_matrizes(melhores):
    fig, eixos = plt.subplots(2, 2, figsize=(10, 9))
    for linha_eixos, melhor in zip(eixos, melhores):
        for ax, sufixo in zip(linha_eixos, ["05", "limite"]):
            matriz = np.array([[melhor[f"tn_{sufixo}"], melhor[f"fp_{sufixo}"]],
                               [melhor[f"fn_{sufixo}"], melhor[f"tp_{sufixo}"]]])
            tela = ConfusionMatrixDisplay(matriz, display_labels=["legítima", "fraude"])
            tela.plot(ax=ax, cmap="Blues", colorbar=False)
            for texto, valor in zip(tela.text_.ravel(), matriz.ravel()):
                texto.set_text(br(f"{valor:,}"))
            limite = 0.5 if sufixo == "05" else melhor["limite"]
            ax.set_title(f"{rotulo(melhor['modelo'], melhor['balanceamento'])}, {melhor['divisao']}\n"
                         f"limite {br(format(limite, '.3f'))}", fontsize=10)
            ax.set_xlabel("Previsto")
            ax.set_ylabel("Real")
    fig.suptitle("Matrizes de confusão no teste: limite 0,5 x limite escolhido na validação")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "matrizes_confusao.png", dpi=150)
    plt.close(fig)


def grafico_importancias(importancias):
    fig, eixos = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    posicoes = np.arange(len(FEATURES))
    largura = 0.38
    for ax, divisao in zip(eixos, DIVISOES):
        parte = importancias[importancias["divisao"] == divisao]
        for i, (_, linha) in enumerate(parte.iterrows()):
            valores = [linha[v] for v in FEATURES]
            barras = ax.bar(posicoes + (i - 0.5) * largura, valores, largura * 0.95,
                            color=CORES[f"rf_{linha['balanceamento']}"],
                            label=rotulo("rf", linha["balanceamento"]))
            ax.bar_label(barras, labels=[br(format(v, ".0%")) for v in valores], fontsize=9, color=CINZA)
        ax.set_xticks(posicoes, FEATURES)
        ax.set_title(f"Divisão {divisao}")
        ax.set_ylim(0, 1)
        ax.grid(axis="y", color="#e5e4e0", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.legend(fontsize=9)
    eixos[0].set_ylabel("Importância (MDI, soma 1)")
    fig.suptitle("Importância das variáveis no Random Forest (agregada por variável original)")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "importancia_variaveis.png", dpi=150)
    plt.close(fig)


def main():
    df = carregar_dados()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    linhas, importancias = [], []
    y_teste, prob_teste = {}, {}  # guardados para os gráficos

    for divisao in DIVISOES:
        _, validacao, teste = dividir(df, divisao)  # o treino não é usado aqui
        y_val = validacao[TARGET].to_numpy()
        y_teste[divisao] = teste[TARGET].to_numpy()
        print(f"\nDivisão {divisao}: validação {len(validacao):,}, teste {len(teste):,}")

        for modelo in MODELOS:
            for balanceamento in BALANCEAMENTOS:
                nome = f"{modelo}_{balanceamento}_{divisao}"
                arquivo = MODELS_DIR / f"{nome}.joblib"
                pipeline = joblib.load(arquivo)
                prob_val = pipeline.predict_proba(validacao[FEATURES])[:, 1]
                prob = pipeline.predict_proba(teste[FEATURES])[:, 1]

                limite = escolher_limite(y_val, prob_val)  # só a validação entra aqui
                linha = {
                    "divisao": divisao, "modelo": modelo, "balanceamento": balanceamento, "nome": nome,
                    "arquivo_mb": round(arquivo.stat().st_size / 1e6, 1),
                    "fraude_validacao": y_val.mean(),
                    "pr_auc_validacao": average_precision_score(y_val, prob_val),
                    "limite": limite,
                    # proporção de fraude do teste = PR-AUC de um palpite aleatório
                    "fraude_teste": y_teste[divisao].mean(),
                    "pr_auc_teste": average_precision_score(y_teste[divisao], prob),
                    "roc_auc_teste": roc_auc_score(y_teste[divisao], prob),
                }
                linha.update(metricas(y_teste[divisao], prob, 0.5, "05"))
                linha.update(metricas(y_teste[divisao], prob, limite, "limite"))
                linhas.append(linha)
                prob_teste[nome] = prob
                if modelo == "rf":
                    importancias.append({"divisao": divisao, "balanceamento": balanceamento,
                                         **importancia_por_variavel(pipeline)})
                print(f"  {nome:<30} PR-AUC validação {linha['pr_auc_validacao']:.4f}  "
                      f"teste {linha['pr_auc_teste']:.4f}  limite {limite:.4f}", flush=True)

                del pipeline  # os RF com SMOTE ocupam centenas de MB; libera antes do próximo
                gc.collect()

    resultados = pd.DataFrame(linhas)
    importancias = pd.DataFrame(importancias)
    resultados.round(4).to_csv(REPORTS_DIR / "metricas.csv", index=False)
    importancias.round(4).to_csv(REPORTS_DIR / "importancia_variaveis.csv", index=False)

    colunas = ["divisao", "modelo", "balanceamento", "pr_auc_validacao", "limite", "fraude_teste",
               "pr_auc_teste", "roc_auc_teste", "precision_limite", "recall_limite", "f1_limite"]
    print("\n" + resultados[colunas].round(4).to_string(index=False))

    # melhor modelo de cada divisão, escolhido só pela validação
    melhores = [escolher_melhor(resultados[resultados["divisao"] == d]) for d in DIVISOES]
    grafico_curvas(resultados, y_teste, prob_teste)
    grafico_matrizes(melhores)
    grafico_importancias(importancias)

    # modelo da aplicação: o melhor da divisão escolhida pelo grupo
    escolhido = next(m for m in melhores if m["divisao"] == DIVISAO_APLICACAO)
    parte = resultados[resultados["divisao"] == DIVISAO_APLICACAO]
    maior = parte.loc[parte["pr_auc_validacao"].idxmax()]
    imp = importancias[(importancias["divisao"] == DIVISAO_APLICACAO)
                       & (importancias["balanceamento"] == escolhido["balanceamento"])]
    joblib.dump({
        "nome": escolhido["nome"],
        "pipeline": joblib.load(MODELS_DIR / f"{escolhido['nome']}.joblib"),
        "limite": float(escolhido["limite"]),
        "pr_auc_validacao": float(escolhido["pr_auc_validacao"]),
        "importancias": imp[FEATURES].iloc[0].to_dict() if escolhido["modelo"] == "rf" else None,
    }, MODELO_APLICACAO)

    print(f"\nModelo da aplicação: {escolhido['nome']} ({escolhido['arquivo_mb']} MB), "
          f"limite {escolhido['limite']:.4f}")
    print(f"  PR-AUC na validação: {escolhido['pr_auc_validacao']:.4f}; maior da divisão "
          f"{DIVISAO_APLICACAO}: {maior['nome']} com {maior['pr_auc_validacao']:.4f} "
          f"(tolerância de desempate: {TOLERANCIA_PR_AUC})")
    print(f"  Salvo em {MODELO_APLICACAO}")
    print(f"Métricas em {REPORTS_DIR / 'metricas.csv'}; figuras em {FIGURES_DIR}")


if __name__ == "__main__":
    main()
