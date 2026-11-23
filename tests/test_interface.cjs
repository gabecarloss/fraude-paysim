// Testa falhas da interface sem navegador ou dependências adicionais.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

async function testar(tipo) {
  const elementos = new Map();
  function elemento(id) {
    if (!elementos.has(id)) elementos.set(id, {
      hidden: false, disabled: false, textContent: "", style: {}, listeners: {},
      addEventListener(nome, funcao) { this.listeners[nome] = funcao; },
      replaceChildren() {}, append() {}, add() {},
      querySelector() { return elemento("botao"); },
    });
    return elementos.get(id);
  }
  const contexto = {
    document: { getElementById: elemento, createElement: () => elemento(Symbol()) },
    Intl, TypeError, SyntaxError, console,
    Option: function () {},
    FormData: class { get(campo) { return {type: "TRANSFER", amount: 100, hour: 5}[campo]; } },
    fetch: async (url) => {
      if (url === "/static/exemplos_demo.json") return {ok: true, json: async () => []};
      if (url.startsWith("/historico")) return tipo === "historico"
        ? {ok: false} : {ok: true, json: async () => []};
      if (tipo === "rede") throw new TypeError("offline");
      if (tipo === "json") return {ok: false, json: async () => { throw new SyntaxError("HTML"); }};
      return {ok: true, json: async () => ({classe: 0, rotulo: "legítima", probabilidade: 0.1,
        limite: 0.9, importancias: []})};
    },
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname, "../app/static/app.js"), "utf8"), contexto);
  await new Promise(resolve => setImmediate(resolve));
  elemento("resultado").hidden = false;
  await elemento("form").listeners.submit({preventDefault() {}});
  assert.equal(elemento("botao").disabled, false);
  if (tipo === "historico") {
    assert.equal(elemento("resultado").hidden, false);
    assert.match(elemento("historico-vazio").textContent, /Não foi possível/);
  } else {
    assert.equal(elemento("resultado").hidden, true);
    assert.equal(elemento("erro").hidden, false);
    assert.match(elemento("erro").textContent, /Falha de comunicação/);
  }
}

(async () => {
  for (const tipo of ["rede", "json", "historico"]) await testar(tipo);
  console.log("3 cenários da interface aprovados");
})().catch(erro => { console.error(erro); process.exitCode = 1; });
