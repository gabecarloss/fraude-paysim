# Roteiro da apresentação

Atualizado a cada etapa do trabalho. No fim, serve de base para gerar os slides.
Apresentação breve: cerca de 10 slides, uma ideia por slide.

Legenda: ✅ pronto · ⏳ pendente · ⚠️ conferir antes de apresentar

---

## 1. Título ✅
- Detecção de Transações Financeiras Fraudulentas com Machine Learning
- Gabriel Pedro Francio e Gabriel Carlos

## 2. Problema e motivação ✅
- Pix: quase 80 bilhões de transações em 2025, alta de 25,7% sobre 2024 (BCB, Relatório de Gestão
  do Pix 2023-2025, p. 14). Dizer "meio de pagamento preferido dos brasileiros" (p. 22) ou "central
  para o varejo" (p. 15), e não "principal": o relatório não usa essa palavra.
- Golpes: perdas de R$ 10,1 bilhões em 2024, contra R$ 8,6 bilhões em 2023, segundo a Febraban
  (Poder360, 12 mar. 2025).
- Objetivo: protótipo que classifica transações como legítimas ou potencialmente fraudulentas.
- Origem: fontes conferidas em 22/10/2026 (ver "Referências" no fim deste arquivo).

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

## 7. Metodologia ✅ (métricas ⏳ Etapa 2)
- Dados divididos antes de qualquer ajuste, em treino / validação / teste:
  - estratificada: 1.773.061 / 443.266 / 554.082 transações (0,30% de fraude nas três)
  - temporal: dias 1–19 / 20–23 / 24–31 → 2.628.113 (0,19%) / 60.569 (1,62%) / 81.727 (2,59%)
- Validação (só do treino) serve para escolher o limite de decisão; o teste só é usado no fim.
- 8 modelos = 2 algoritmos × 2 balanceamentos × 2 divisões:
  - Random Forest (principal) × Regressão Logística (comparação)
  - `class_weight="balanced"` × SMOTE (equilibra 1:1); nunca os dois juntos
- Tudo num Pipeline: one-hot em `type`, padronização de `amount` e `hour`, SMOTE (só no treino), modelo.
- Hiperparâmetros simples, sem busca: RF com 100 árvores e folhas com no mínimo 50 transações; LR padrão.
- Decisões do grupo: sem amostragem das legítimas (usamos o treino inteiro); `hour` numérico também na
  LR, como na proposta (ela não captura o pico da madrugada; ver slide 8).
- Custo: o SMOTE dobra o treino (de 1,77 para 3,54 milhões de linhas na estratificada). Tempo total de
  34 min; os RF com SMOTE levaram 554 s e 901 s e geraram arquivos de 439 e 647 MB. As LR levaram até 10 s.
- Métricas (Etapa 2): PR-AUC (principal), ROC-AUC, Precision, Recall, F1, matriz de confusão e limite.
- Origem: `python -m src.train`, executado em 23/10/2026 (8 CPUs); tempos em `reports/tempos_treino.csv`.

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
- LGPD, art. 20: direito de pedir revisão de decisões tomadas unicamente por tratamento automatizado,
  por isso a ferramenta é só de apoio. Não dizer que a lei exige revisão por um humano: essa parte
  foi retirada pela Lei nº 13.853/2019.
- Falsos positivos prejudicam clientes legítimos; falsos negativos deixam fraudes passarem
  (⏳ números da matriz de confusão).
- A base é simulada e não brasileira, tem artefatos do simulador (teto de 10 milhões nas fraudes,
  queda das legítimas a partir do dia 18) e a proporção de fraude muda ao longo do tempo (slide 6).
- Alternativa considerada: IEEE-CIS Fraud Detection (Vesta/Kaggle), com dados reais de e-commerce.
  Não foi usada porque a maior parte das variáveis é anonimizada (o usuário não conseguiria preenchê-las
  na aplicação), trata de outro tipo de fraude (compra com cartão) e também não é brasileira.
  Além disso, as regras da competição limitam o uso a fins não comerciais.

## 11. Conclusão ⏳
- Responder: qual modelo e qual forma de tratar o desbalanceamento funcionaram melhor, e o que
  isso significa na prática.
- Próximos passos possíveis: base real, mais variáveis, validação com especialistas.

---

## Referências (conferidas em 22/10/2026)

Já corrigidas em relação à proposta. As que entram nos slides vão para um slide final de referências.

- BANCO CENTRAL DO BRASIL. **Relatório de Gestão do Pix 2023-2025**. Brasília: BCB, 2026. Disponível em:
  https://www.bcb.gov.br/content/estabilidadefinanceira/pix/relatorio_de_gestao_pix/relatorio_gestao_pix_2026.pdf.
  Acesso em: 22 out. 2026.
- BRASIL. Lei nº 13.709, de 14 de agosto de 2018. Lei Geral de Proteção de Dados Pessoais (LGPD).
  **Diário Oficial da União**, Brasília, DF, 15 ago. 2018.
- BREIMAN, Leo. Random forests. **Machine Learning**, v. 45, n. 1, p. 5-32, 2001. DOI: 10.1023/A:1010933404324.
- CHAWLA, Nitesh V. *et al*. SMOTE: synthetic minority over-sampling technique. **Journal of Artificial
  Intelligence Research**, v. 16, p. 321-357, 2002. DOI: 10.1613/jair.953.
- IEEE COMPUTATIONAL INTELLIGENCE SOCIETY. **IEEE-CIS Fraud Detection**. [S. l.]: Kaggle, 2019. Disponível em:
  https://www.kaggle.com/competitions/ieee-fraud-detection. Acesso em: 22 out. 2026.
- LE BORGNE, Yann-Aël *et al*. **Reproducible machine learning for credit card fraud detection**: practical
  handbook. Bruxelas: Université Libre de Bruxelles, 2022. Disponível em:
  https://fraud-detection-handbook.github.io/fraud-detection-handbook/. Acesso em: 22 out. 2026.
  (O livro *aplica* o reamostramento só nos dados de treino, com Pipeline do imblearn; não traz uma
  frase dizendo que isso é obrigatório.)
- LOPEZ-ROJAS, Edgar. **Synthetic Financial Datasets For Fraud Detection**. Kaggle, 2017. Disponível em:
  https://www.kaggle.com/datasets/ealaxi/paysim1. Acesso em: 22 out. 2026.
  (As contagens 6.362.620 / 8.213 vêm da nossa leitura do CSV, não da descrição da base. A descrição
  fala em 744 passos, cerca de 30 dias, mas o CSV vai do step 1 ao 743.)
- LOPEZ-ROJAS, Edgar Alonso; ELMIR, Ahmad; AXELSSON, Stefan. PaySim: a financial mobile money simulator
  for fraud detection. In: EUROPEAN MODELING AND SIMULATION SYMPOSIUM, 28., 2016, Larnaca.
  **Proceedings** [...]. 2016. p. 249-255. ISBN 978-88-97999-76-8.
- PODER360. Golpes causaram prejuízo de R$ 10,1 bi em 2024, diz Febraban. **Poder360**, Brasília,
  12 mar. 2025. Disponível em:
  https://www.poder360.com.br/poder-economia/golpes-causaram-prejuizo-de-r-101-bi-em-2024-diz-febraban/.
  Acesso em: 22 out. 2026.
