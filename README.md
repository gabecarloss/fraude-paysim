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

Ambiente previsto: Python 3.12. Execute os comandos na raiz do projeto.

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

O `src.train` treina 8 modelos. A execução original levou cerca de 34 minutos numa máquina
com 8 núcleos (`reports/tempos_treino_2026-10-23.csv`). Na nova execução de 23/11/2026,
a soma dos tempos de ajuste registrados foi de 633,8 segundos, cerca de 10,6 minutos
(`reports/tempos_treino.csv`); isso não inclui preparação, avaliação e gravação dos arquivos.
Os tempos dependem da máquina e do ambiente. Os modelos ocupam cerca de 1,2 GB em `models/`, quase
tudo nos dois Random Forest com SMOTE.

## Continuidade do trabalho e alterações realizadas

O trabalho anterior do grupo foi mantido: preparação do PaySim, análise exploratória,
divisões estratificada e temporal, oito pipelines de treinamento, avaliação, escolha do
limite, API de classificação e histórico SQLite. Os scripts de modelagem em `src/`
não foram alterados nesta etapa. Também foram preservadas as três entradas (`type`,
`amount`, `hour`), os algoritmos, os balanceamentos e os critérios de seleção.

As alterações acrescentaram duas formas de fornecer entradas fictícias à aplicação:
um gerador com Ollama local e seis exemplos fixos selecionáveis. Isso permite verificar
o fluxo da interface sem digitar cada transação. A LLM só gera entradas; a classificação
continua sendo feita pelo pipeline treinado anteriormente definido pelo grupo.
Também foram corrigidos o tratamento de importâncias ausentes, as mensagens de falha
de comunicação e a rejeição de modelos remotos no gerador, com testes de regressão.

### Por que o treinamento foi executado novamente

Nesta cópia do repositório, os dados e os arquivos treinados estavam ausentes: são
ignorados pelo Git. Isso não significa que o treinamento anterior estivesse errado
ou que o trabalho precisasse ser substituído. O `modelo_aplicacao.joblib` era necessário
para executar e testar a aplicação, mas não estava disponível para cópia.

Por isso, o grupo baixou novamente o CSV original do PaySim e executou os scripts
existentes de preparação, treinamento e avaliação em 23/11/2026. O objetivo foi regenerar
os artefatos locais com a metodologia existente. Não houve treinamento com exemplos
da LLM, troca de base ou adaptação para o Brasil.

A nova avaliação reproduziu as métricas anteriormente registradas, nas quatro casas
decimais apresentadas. O escolhido continuou sendo `rf_classweight_estratificada`, com
PR-AUC de validação 0,3464, PR-AUC de teste 0,3619 e limite 0,9886. A Precision no teste
foi 0,5651 e o Recall 0,3274. Origem: execução de `src.evaluate` e `reports/metricas.csv`.
O arquivo `models/modelo_aplicacao.joblib` foi regenerado e continua fora do Git.
Os tempos da execução anterior foram preservados em arquivo separado para manter
a origem dos números históricos do trabalho.

## Decisões principais

- Apenas transações `TRANSFER` e `CASH_OUT` (as únicas com fraude).
- Entradas do modelo: tipo, valor e hora do dia (`step % 24`).
- Colunas de saldo excluídas (vazam o rótulo) e identificadores de conta não usados.
- Random Forest como modelo principal, Regressão Logística como comparação.
- Desbalanceamento tratado com `class_weight` e SMOTE, só no treino, dentro de um Pipeline.
- Métricas: Precision, Recall, F1, matriz de confusão, PR-AUC e ROC-AUC.

## Entradas fictícias para testes da aplicação

### Exemplos prontos (sem depender da LLM)

A tela oferece seis transações fictícias em `app/static/exemplos_demo.json`.
Escolha um exemplo e clique em **Analisar**. Os valores não são convertidos para reais.
Os exemplos variam tipo, valor e hora, permitindo observar como a previsão muda.
Não possuem rótulo verdadeiro, escore pré-programado ou garantia de alerta; a resposta
vem do classificador carregado. Não entram no treinamento nem no cálculo das métricas.
O classificador treinado continua obrigatório para iniciar a API.

### Geração com Ollama

A interface inclui um gerador de transações fictícias via Ollama. Ele usa a API local
`http://127.0.0.1:11434/api/chat`, sem bibliotecas Python adicionais. Instale o Ollama
a partir de https://ollama.com/download/windows e baixe antecipadamente um modelo local
compatível com saídas estruturadas. O download inicial exige internet.
O desempenho depende do modelo e do computador.

Modelo usado no teste local: `qwen2.5:1.5b`. Para preparar esse mesmo modelo:

```powershell
ollama pull qwen2.5:1.5b
ollama list
```

1. Abra o Ollama e execute `ollama list` para conferir o nome do modelo instalado.
2. Tenha `models/modelo_aplicacao.joblib` disponível (gerado pelo treinamento e avaliação).
3. Inicie a aplicação com `uvicorn app.main:app --reload`.
4. Na tela, informe o nome exato do modelo local e descreva um cenário.
5. Clique em **Gerar transação fictícia**, revise os campos e clique em **Analisar**.

A LLM gera apenas tipo, valor, hora e descrição. O Random Forest faz a classificação.
A geração não grava no histórico; ao clicar em Analisar, o fluxo normal salva a análise
no SQLite. Use um banco de demonstração separado de qualquer registro real.
As entradas geradas não entram no treino, nas métricas ou na base PaySim. Não possuem
rótulo verdadeiro e não permitem medir acurácia. Não há garantia de obter um alerta.
O modelo e os cenários da demonstração mantêm os campos do PaySim: `type`, `amount`
e `hour`, com os tipos `TRANSFER` e `CASH_OUT`. O valor não recebe conversão de moeda.

Se o Ollama estiver indisponível, a interface informa o erro. Como alternativa manual,
use o seletor de exemplos prontos. Não há substituição automática da LLM por dados
pré-programados.

### Artefato necessário

A API exige `models/modelo_aplicacao.joblib`: um arquivo exportado por `src.evaluate`
com pipeline, limite de decisão e importâncias. Os arquivos de `models/` são ignorados
pelo Git; clonar o repositório não fornece o classificador treinado.
Obtenha o artefato com o grupo que executou o treinamento ou gere-o com os comandos
de preparação, treino e avaliação da seção Execução. Não basta executar a avaliação
sem os oito modelos treinados que ela carrega.

### Validação técnica e pendências

- Verificada a sintaxe de `app/gerador.py`, `app/main.py` e `app/static/app.js`.
- Verificados os seis exemplos: tipos permitidos, valores positivos e horas inteiras de 0 a 23.
- Em 23/11/2026, uma chamada direta à API local do Ollama com `qwen2.5:1.5b`
  retornou `TRANSFER`, valor 500 e hora 23. Isso valida apenas a geração de campos:
  não comprova fidelidade ao cenário pedido, qualidade do classificador ou integração completa.
- A chamada direta não executou o endpoint Python `/gerar-cenario`.
- Após as correções da revisão, cinco testes Python e três cenários da interface
  passaram. Cobrem bloqueio de aliases remotos antes do envio do cenário, respostas
  inválidas, indisponibilidade do Ollama, importâncias ausentes e falhas de comunicação.
- A função real `gerar_cenario` também foi executada com `qwen2.5:1.5b`, retornando
  `TRANSFER`, valor 1000 e hora 2. O endpoint e o classificador não participaram desse teste.
- Os testes automatizados foram executados com Python 3.15 na `.venv`. Depois,
  o usuário instalou as dependências e executou preparação, treino e avaliação.
- Teste manual em 23/11/2026, confirmado pelo usuário: geração com `qwen2.5:1.5b`
  pela interface, classificação e consulta das análises no histórico.
  As capturas do histórico mostram `CASH_OUT`, 50.000, 14h → legítima (0,00%, arredondado);
  `TRANSFER`, 1.000, 0h → legítima (88,55%); e `TRANSFER`, 1.000.000, 5h → potencial
  fraude (99,61%). São saídas do classificador para entradas fictícias, sem rótulo verdadeiro.
- Pendente: repetir os casos de entrada inválida na API em execução. Os testes
  automatizados cobrem cenários específicos e não garantem ausência de todos os erros.

O roteiro preserva as análises e execuções anteriores do grupo. Os testes manuais
atuais confirmam o fluxo básico completo; não demonstram validade para transações reais.

Para repetir os testes de regressão na raiz do projeto, com as dependências instaladas:

```powershell
python -m unittest discover -s tests -v
node tests/test_interface.cjs
```

O teste da interface usa Node.js e simula respostas de rede, sem dependências npm.
Os testes Python simulam o Ollama e não precisam do artefato treinado. O gerador consulta
`/api/show` antes de enviar o cenário e rejeita modelos remotos ou sem metadados locais.

## Limitações

A base é simulada e não é brasileira; os resultados não devem ser usados isoladamente em
decisões financeiras reais.

Na base, as transações legítimas caem muito a partir do dia 18, enquanto as fraudes seguem
constantes. Com o corte temporal escolhido (treino nos dias 1 a 23, teste nos dias 24 a 31), o teste
tem cerca de 2,6% de fraude e o treino cerca de 0,23%. Por isso, Precision e PR-AUC da divisão
temporal não são comparáveis diretamente com as da divisão estratificada. Detalhes em
`notebooks/01_analise_exploratoria.ipynb`.
