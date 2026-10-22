# Roteiro da apresentação

Atualizado a cada etapa do trabalho. No fim, serve de base para gerar os slides.
Apresentação breve: cerca de 10 slides, uma ideia por slide.

Legenda: ✅ pronto · ⏳ pendente · ⚠️ conferir antes de apresentar

---

## 1. Título ✅
- Detecção de Transações Financeiras Fraudulentas com Machine Learning
- Gabriel Pedro Francio e Gabriel Carlos

## 2. Problema e motivação ⚠️
- O Pix virou o principal meio de pagamento do Brasil, e as perdas com fraude são altas.
- Objetivo: protótipo que classifica transações como legítimas ou potencialmente fraudulentas.
- ⚠️ Os números da proposta (quase 80 bi de transações Pix em 2025, segundo o BCB; R$ 10,1 bi de
  perdas em 2024, segundo a Febraban/Poder360) precisam ser conferidos nas fontes antes de entrar no slide.

## 3. Base de dados ✅
- PaySim (Kaggle): simulada a partir de dados reais de um serviço de dinheiro móvel africano.
- Por que essa base: as variáveis são compreensíveis (tipo, valor, hora), então o usuário consegue
  digitar uma transação na aplicação. Dados brasileiros rotulados não são públicos (sigilo bancário e LGPD).
- Usamos só TRANSFER e CASH_OUT, os únicos tipos com fraude:
  - 2.770.409 transações, das quais 8.213 são fraudes (0,296%)
  - CASH_OUT: 2.233.384 legítimas / 4.116 fraudes (0,184%)
  - TRANSFER: 528.812 legítimas / 4.097 fraudes (0,769%)
- Um modelo que nunca aponta fraude acertaria 99,70%: por isso a acurácia não serve.
- Origem: `python -m src.prepare_data` e `notebooks/01_analise_exploratoria.ipynb`, executados em 22/10/2026.

## 4. Decisões sobre as variáveis ✅
- Entradas do modelo: `type`, `amount` e `hour` (hora do dia = `step % 24`).
- Colunas de saldo excluídas: as fraudes são canceladas, então o saldo "entrega" a resposta (vazamento).
- Identificadores de conta não usados.

## 5. O que os dados mostram ✅
- Figuras: `reports/figures/hora_por_classe.png` e `reports/figures/valor_por_classe.png`.
- **Hora:** as fraudes acontecem em quantidade parecida em todas as horas (cerca de 270 a 380 por
  hora); as legítimas se concentram de dia. De madrugada a proporção de fraude dispara (57,9% às 5h,
  contra 0,11% a 0,28% entre 9h e 20h). Pode ser em parte efeito do simulador.
- **Valor:** as fraudes tendem a ser maiores (mediana de cerca de 441 mil, contra cerca de 171 mil
  nas legítimas), mas com muita sobreposição. Nenhuma fraude passa de 10 milhões (287 fraudes têm
  exatamente esse valor), enquanto 2.443 legítimas passam: provável limite do simulador.
- Origem: `notebooks/01_analise_exploratoria.ipynb`, executado em 22/10/2026.

## 6. Divisão temporal e sua limitação ✅
- Figura: `reports/figures/transacoes_por_dia.png`.
- As fraudes são constantes (216 a 320 por dia) nos 31 dias. As legítimas despencam a partir do
  dia 18 (de 150 a 250 mil por dia para até 24 mil), e o dia 31 só tem fraudes.
- Decisão do grupo: manter o corte (treino nos dias 1 a 23, teste nos dias 24 a 31) e registrar a
  limitação:
  - treino: 2.682.589 legítimas / 6.093 fraudes (0,23% de fraude)
  - teste: 79.607 legítimas / 2.120 fraudes (2,59% de fraude)
- Mensagem do slide: Precision e PR-AUC dependem da proporção de fraude, então os modelos são
  comparados dentro de cada divisão, não uma divisão contra a outra.
- Origem: `notebooks/01_analise_exploratoria.ipynb`, executado em 22/10/2026.

## 7. Metodologia ⏳
- Divisão treino/teste estratificada e temporal, feita antes de qualquer ajuste.
- Random Forest (principal) × Regressão Logística (comparação).
- Desbalanceamento: `class_weight` × SMOTE, só no treino e dentro de um Pipeline.
- Métricas: PR-AUC (principal), ROC-AUC, Precision, Recall, F1, matriz de confusão e limite de decisão.

## 8. Resultados ⏳
- Tabela comparativa dos modelos (aguarda `src.train` e `src.evaluate`).
- Curva Precision × Recall e limite escolhido.
- Importância das variáveis do Random Forest.
- Explicar a diferença RF × LR à luz do slide 5: o risco por hora não é linear (sobe de madrugada),
  o que favorece o Random Forest.

## 9. Aplicação ⏳
- Demonstração: o usuário informa tipo, valor e hora e recebe a classe, a probabilidade e as
  variáveis mais importantes.
- Aviso na tela: ferramenta de apoio à análise, não de bloqueio.

## 10. Ética e limitações ✅ (resultados de FP/FN ⏳)
- LGPD, art. 20: direito à revisão de decisões automatizadas, por isso a ferramenta é só de apoio.
- Falsos positivos prejudicam clientes legítimos; falsos negativos deixam fraudes passarem
  (⏳ números da matriz de confusão).
- A base é simulada e não brasileira, tem artefatos do simulador (teto de 10 milhões nas fraudes,
  queda das legítimas a partir do dia 18) e a proporção de fraude muda ao longo do tempo (slide 6).
- Alternativa considerada: IEEE-CIS Fraud Detection (Vesta/Kaggle), com dados reais de e-commerce.
  Não foi usada porque a maior parte das variáveis é anonimizada (o usuário não conseguiria preenchê-las
  na aplicação), trata de outro tipo de fraude (compra com cartão) e também não é brasileira.
  ⏳ Incluir a referência em ABNT a partir da página oficial da competição.

## 11. Conclusão ⏳
- Responder: qual modelo e qual forma de tratar o desbalanceamento funcionaram melhor, e o que
  isso significa na prática.
- Próximos passos possíveis: base real, mais variáveis, validação com especialistas.
