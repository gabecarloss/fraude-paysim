const form = document.getElementById("form");
const resultado = document.getElementById("resultado");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
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

  resultado.textContent = JSON.stringify(await resposta.json(), null, 2);
});
