const form = document.getElementById("form");
const erro = document.getElementById("erro");
const resultado = document.getElementById("resultado");

async function carregarExemplos() {
  const seletor = document.getElementById("exemplo-demo");
  const estado = document.getElementById("estado-demo");
  try {
    const resposta = await fetch("/static/exemplos_demo.json");
    if (!resposta.ok) throw new Error("Falha ao carregar os exemplos.");
    const exemplos = await resposta.json();
    seletor.replaceChildren(new Option("Escolha um exemplo", ""));
    exemplos.forEach((exemplo, indice) => seletor.add(new Option(exemplo.descricao, String(indice))));
    seletor.disabled = false;
    seletor.addEventListener("change", () => {
      if (seletor.value === "") return;
      const exemplo = exemplos[Number(seletor.value)];
      for (const campo of ["type", "amount", "hour"]) form.elements[campo].value = exemplo[campo];
      resultado.hidden = true;
      erro.hidden = true;
      document.getElementById("origem-entrada").textContent =
        `Exemplo fictício: ${exemplo.descricao}. Sem rótulo verdadeiro de fraude.`;
      estado.textContent = "Formulário preenchido. Clique em Analisar para consultar o classificador real.";
    });
  } catch (falha) {
    estado.textContent = "Não foi possível carregar os exemplos. Você pode preencher a transação manualmente.";
  }
}

carregarExemplos();

// Números no formato brasileiro. Escore com 2 casas para não parecer igual ao limite quando não é.
const porcento = new Intl.NumberFormat("pt-BR", { style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2 });
const porcentoCurto = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 0 });
const valor = new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

// Mensagens para os erros de validação (422) que o FastAPI devolve, por campo
const MENSAGENS = {
  type: "O tipo deve ser TRANSFER ou CASH_OUT.",
  amount: "O valor deve ser um número maior que zero.",
  hour: "A hora deve ser um número inteiro entre 0 e 23.",
};

function rotuloClasse(classe) {
  return classe === 1 ? "potencial fraude" : "legítima";
}

function mostrarResultado(dados) {
  const selo = document.getElementById("classe");
  selo.textContent = dados.rotulo;
  selo.className = dados.classe === 1 ? "selo fraude" : "selo legitima";
  document.getElementById("probabilidade").textContent = porcento.format(dados.probabilidade);
  document.getElementById("limite").textContent = porcento.format(dados.limite);

  const lista = document.getElementById("importancias");
  lista.replaceChildren();
  for (const item of dados.importancias) {
    const linha = document.createElement("li");
    const nome = document.createElement("span");
    nome.textContent = item.variavel;
    const trilho = document.createElement("span");
    trilho.className = "trilho";
    const barra = document.createElement("span");
    barra.className = "barra";
    barra.style.width = `${item.importancia * 100}%`;
    trilho.append(barra);
    const numero = document.createElement("span");
    numero.textContent = porcentoCurto.format(item.importancia);
    linha.append(nome, trilho, numero);
    lista.append(linha);
  }
  resultado.hidden = false;
}

async function carregarHistorico() {
  const resposta = await fetch("/historico?quantidade=10");
  if (!resposta.ok) throw new Error("Não foi possível carregar o histórico.");
  const analises = await resposta.json();
  const corpo = document.getElementById("historico");
  corpo.replaceChildren();
  for (const a of analises) {
    const linha = document.createElement("tr");
    const celulas = [
      a.data_hora,
      a.type,
      valor.format(a.amount),
      `${a.hour}h`,
      porcento.format(a.probabilidade),
      rotuloClasse(a.classe),
    ];
    for (const texto of celulas) {
      const celula = document.createElement("td");
      celula.textContent = texto;
      linha.append(celula);
    }
    if (a.classe === 1) linha.className = "linha-fraude";
    corpo.append(linha);
  }
  document.getElementById("historico-vazio").hidden = analises.length > 0;
}

function mostrarFalhaHistorico() {
  const aviso = document.getElementById("historico-vazio");
  aviso.hidden = false;
  aviso.textContent = "Não foi possível carregar o histórico.";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  erro.hidden = true;
  resultado.hidden = true;
  const botao = form.querySelector('button[type="submit"]');
  botao.disabled = true;
  try {
    const dados = new FormData(form);
    const resposta = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type: dados.get("type"),
        amount: Number(dados.get("amount")),
        hour: Number(dados.get("hour")),
      }),
    });
    const corpo = await resposta.json();
    if (!resposta.ok) {
      const campos = Array.isArray(corpo.detail) ? corpo.detail.map((e) => e.loc.at(-1)) : [];
      const textos = [...new Set(campos)].map((c) => MENSAGENS[c] ?? `Entrada inválida: ${c}.`);
      throw new Error(textos.length ? textos.join(" ") : "Não foi possível analisar a transação.");
    }
    mostrarResultado(corpo);
    await carregarHistorico().catch(mostrarFalhaHistorico);
  } catch (falha) {
    resultado.hidden = true;
    erro.textContent = falha instanceof TypeError || falha instanceof SyntaxError
      ? "Falha de comunicação com a aplicação. Confira se o servidor está funcionando."
      : falha.message;
    erro.hidden = false;
  } finally {
    botao.disabled = false;
  }
});

carregarHistorico().catch(mostrarFalhaHistorico);

document.getElementById("form-gerador").addEventListener("submit", async (event) => {
  event.preventDefault();
  const botao = document.getElementById("botao-gerador");
  const estado = document.getElementById("estado-gerador");
  const campos = new FormData(event.currentTarget);
  botao.disabled = true;
  estado.textContent = "Gerando no computador local. O primeiro carregamento pode demorar…";
  try {
    const resposta = await fetch("/gerar-cenario", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modelo: campos.get("modelo"), pedido: campos.get("pedido") }),
    });
    const dados = await resposta.json();
    if (!resposta.ok) {
      throw new Error(typeof dados.detail === "string" ? dados.detail : "Confira o nome do modelo e o cenário.");
    }
    for (const campo of ["type", "amount", "hour"]) form.elements[campo].value = dados[campo];
    resultado.hidden = true;
    document.getElementById("origem-entrada").textContent =
      `Entrada fictícia gerada por LLM local (${dados.modelo_gerador}). Não possui rótulo real de fraude.`;
    estado.textContent = `Cenário fictício: ${dados.descricao} Revise os campos e clique em Analisar.`;
  } catch (falha) {
    estado.textContent = falha instanceof TypeError ? "Falha de conexão com a aplicação." : falha.message;
  } finally {
    botao.disabled = false;
  }
});
