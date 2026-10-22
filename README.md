# Detecção de Transações Financeiras Fraudulentas com Machine Learning

Protótipo educacional que classifica transações como legítimas ou potencialmente
fraudulentas usando a base pública PaySim, com uma aplicação web simples para demonstração.

**Grupo:** Gabriel Pedro Francio, Gabriel Carlos

## Estrutura

```
app/            servidor FastAPI e interface (HTML/CSS/JS em app/static)
data/raw/       CSV original do Kaggle (não versionado)
data/processed/ dados filtrados prontos para o treino
docs/           roteiro da apresentação
models/         modelos treinados (.joblib)
notebooks/      análise exploratória
reports/        métricas e gráficos gerados
src/            preparação dos dados, treino e avaliação
```

## Configuração (Windows / PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Se o PowerShell bloquear a ativação, rode uma vez:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## Base de dados

1. Baixe a base em https://www.kaggle.com/datasets/ealaxi/paysim1 (precisa de conta no Kaggle).
2. Extraia o arquivo `PS_20174392719_1491204439457_log.csv` para `data/raw/`.

## Execução

```powershell
python -m src.prepare_data     # filtra TRANSFER/CASH_OUT e gera data/processed/
python -m src.train            # treina os modelos e salva em models/
python -m src.evaluate         # gera métricas em reports/
uvicorn app.main:app --reload  # abre a aplicação em http://127.0.0.1:8000
```

## Decisões principais

- Apenas transações `TRANSFER` e `CASH_OUT` (as únicas com fraude).
- Entradas do modelo: tipo, valor e hora do dia (`step % 24`).
- Colunas de saldo excluídas (vazam o rótulo) e identificadores de conta não usados.
- Random Forest como modelo principal, Regressão Logística como comparação.
- Desbalanceamento tratado com `class_weight` e SMOTE, só no treino, dentro de um Pipeline.
- Métricas: Precision, Recall, F1, matriz de confusão, PR-AUC e ROC-AUC.

## Limitações

A base é simulada e não é brasileira; os resultados não devem ser usados isoladamente em
decisões financeiras reais.

Na base, as transações legítimas caem muito a partir do dia 18, enquanto as fraudes seguem
constantes. Com o corte temporal escolhido (treino nos dias 1 a 23, teste nos dias 24 a 31), o teste
tem cerca de 2,6% de fraude e o treino cerca de 0,23%. Por isso, Precision e PR-AUC da divisão
temporal não são comparáveis diretamente com as da divisão estratificada. Detalhes em
`notebooks/01_analise_exploratoria.ipynb`.
