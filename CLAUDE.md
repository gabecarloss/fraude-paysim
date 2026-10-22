# CLAUDE.md

Trabalho acadêmico de detecção de fraudes com a base PaySim (Kaggle, ealaxi/paysim1).
Grupo: Gabriel Pedro Francio e Gabriel Carlos. A proposta aprovada pelo professor define o
escopo; estas regras existem para não fugir dela.

## Git
- **Nunca fazer commit.** Também não fazer `git add`, `push`, `merge`, `rebase`, `reset`,
  `stash`, nem criar branch ou tag. Quem versiona é o grupo.
- Comandos só de leitura (`git status`, `git diff`, `git log`) são permitidos.
- Se pedirem, sugerir a mensagem de commit em texto, sem executar.

## Idioma
- Responder, comentar código e escrever documentação em português.
- Nomes de colunas da base ficam como no original (`type`, `amount`, `step`, `isFraud`).

## Escopo definido na proposta (não mudar sem perguntar)
- Usar apenas transações `TRANSFER` e `CASH_OUT`.
- Entradas do modelo: `type`, `amount` e `hour` (`step % 24`).
- Nunca usar as colunas de saldo (`oldbalanceOrg`, `newbalanceOrig`, `oldbalanceDest`,
  `newbalanceDest`): vazam o rótulo. Nunca usar `nameOrig`/`nameDest` nem `isFlaggedFraud`.
- Modelo principal: Random Forest. Comparação: Regressão Logística.
- Desbalanceamento: `class_weight` e SMOTE, comparados entre si.
- Ferramentas: Python, Pandas, NumPy, Scikit-learn, imbalanced-learn, joblib, FastAPI,
  front em HTML/CSS/JS puro, SQLite opcional para guardar testes.
- Qualquer mudança de metodologia (outro modelo, outra feature, outra base) precisa de
  confirmação do usuário antes, pois altera o que foi entregue ao professor.

## Rigor metodológico
- Dividir treino/teste **antes** de qualquer ajuste. Duas divisões: estratificada e temporal
  (por `step`, treino nos primeiros dias, teste nos últimos).
- SMOTE e qualquer pré-processamento ficam dentro de `imblearn.pipeline.Pipeline` e só
  recebem `fit` nos dados de treino. Nada do teste pode influenciar o modelo.
- Acurácia não é métrica principal. Reportar Precision, Recall, F1, matriz de confusão,
  PR-AUC (principal) e ROC-AUC (apoio), e o ajuste do limite de decisão.
- Usar `RANDOM_STATE` e os caminhos de `src/config.py`; não repetir constantes nos scripts.
- Números citados em relatório, README ou apresentação devem vir de uma execução real,
  nunca estimados ou inventados. Se ainda não foi rodado, dizer isso.

## Dados
- Não inventar, simular nem gerar dados. A única base é o CSV do PaySim em `data/raw/`.
- O download do Kaggle é feito pelo grupo (precisa de conta).
- Base grande (~6,3 milhões de linhas, ~470 MB): ler com `usecols`, trabalhar a partir do
  parquet em `data/processed/` e, se o treino ficar pesado, amostrar só as legítimas
  (previsto na proposta), deixando isso registrado.

## Ética e aplicação
- A aplicação é ferramenta de apoio à análise, não de bloqueio ou acusação (LGPD, art. 20).
  Manter o aviso na interface.
- Discutir falsos positivos e falsos negativos nos resultados.
- Sempre lembrar que a base é simulada e não brasileira.

## Forma de trabalhar
- É um trabalho educacional: o grupo precisa entender e apresentar tudo. Explicar o porquê
  das decisões, preferir código simples e legível, sem abstrações desnecessárias.
- Avançar por etapas, nesta ordem: dados → treino → implementação → app → docs, sem
  implementar etapas inteiras que não foram pedidas. As semanas do cronograma da proposta
  são só ilustrativas; não usar como prazo.
- Referências em documentos seguem ABNT. Nunca inventar referência, autor ou dado estatístico.
- Perguntar antes de adicionar dependência nova; se aprovada, incluir em `requirements.txt`.

## Ambiente
- Windows, PowerShell, Python 3.12, ambiente em `.venv` na raiz
  (`.\.venv\Scripts\Activate.ps1`).
- Rodar scripts da raiz como módulo: `python -m src.prepare_data`, `python -m src.train`,
  `python -m src.evaluate`, `uvicorn app.main:app --reload`.
- Não versionar `data/`, `models/`, `.venv/` nem `*.db` (já no `.gitignore`).
