const form = document.getElementById("form");
const erro = document.getElementById("erro");
const resultado = document.getElementById("resultado");

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

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  erro.hidden = true;
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
    // No 422, cada erro traz o campo em loc (ex.: ["body", "hour"])
    const campos = Array.isArray(corpo.detail) ? corpo.detail.map((e) => e.loc.at(-1)) : [];
    const textos = [...new Set(campos)].map((c) => MENSAGENS[c] ?? `Entrada inválida: ${c}.`);
    erro.textContent = textos.length ? textos.join(" ") : "Não foi possível analisar a transação.";
    erro.hidden = false;
    resultado.hidden = true;
    return;
  }

  mostrarResultado(corpo);
  carregarHistorico();
});

carregarHistorico();
