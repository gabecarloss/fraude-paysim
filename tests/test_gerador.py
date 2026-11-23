"""Regressões do gerador; sem download, classificador ou conexão externa."""

import ast
import io
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError

from fastapi import HTTPException

from app.gerador import PedidoCenario, gerar_cenario


class TestGerador(unittest.TestCase):
    def setUp(self):
        self.pedido = PedidoCenario(modelo="modelo-teste", pedido="Uma transferência fictícia")
        self.local = {"model_info": {"general.architecture": "qwen2"}}

    def executar(self, respostas):
        cliente = Mock()
        cliente.open.side_effect = [
            io.BytesIO(json.dumps(r).encode()) if isinstance(r, dict) else r
            for r in respostas
        ]
        with patch("app.gerador.build_opener", return_value=cliente):
            resultado = gerar_cenario(self.pedido)
        return resultado, cliente

    def test_modelo_local_gera_campos_validados(self):
        entrada = {"type": "TRANSFER", "amount": 500, "hour": 5, "descricao": "Cenário fictício"}
        resultado, cliente = self.executar([self.local, {"message": {"content": json.dumps(entrada)}}])
        self.assertTrue(resultado["ficticio"])
        self.assertEqual(resultado["hour"], 5)
        self.assertEqual(cliente.open.call_count, 2)

    def test_alias_remoto_bloqueado_antes_do_envio_do_cenario(self):
        for metadados in [
            {**self.local, "remote_host": "https://ollama.com"},
            {**self.local, "remote_model": "modelo-remoto"},
            {},
        ]:
            with self.subTest(metadados=metadados):
                cliente = Mock()
                cliente.open.return_value = io.BytesIO(json.dumps(metadados).encode())
                with patch("app.gerador.build_opener", return_value=cliente):
                    with self.assertRaises(HTTPException) as erro:
                        gerar_cenario(self.pedido)
                self.assertEqual(erro.exception.status_code, 422)
                self.assertEqual(cliente.open.call_count, 1)
                requisicao = cliente.open.call_args.args[0]
                self.assertTrue(requisicao.full_url.endswith("/api/show"))
                self.assertNotIn("messages", json.loads(requisicao.data))

    def test_resposta_invalida_retorna_502(self):
        for conteudo in ["{", '{"type":"TRANSFER","amount":10,"hour":25,"descricao":"Teste"}']:
            with self.subTest(conteudo=conteudo):
                with self.assertRaises(HTTPException) as erro:
                    self.executar([self.local, {"message": {"content": conteudo}}])
                self.assertEqual(erro.exception.status_code, 502)

    def test_ollama_indisponivel_e_modelo_ausente_retornam_503(self):
        for falha in [URLError("offline"), HTTPError("local", 404, "ausente", {}, None)]:
            with self.subTest(falha=falha):
                with self.assertRaises(HTTPException) as erro:
                    self.executar([falha])
                self.assertEqual(erro.exception.status_code, 503)

    def test_importancias_ausentes_nao_quebram_a_montagem(self):
        # Executa a expressão real sem carregar o classificador nem criar o banco.
        arquivo = Path(__file__).resolve().parents[1] / "app" / "main.py"
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
        atribuicao = next(n for n in arvore.body if isinstance(n, ast.Assign)
                          and any(isinstance(t, ast.Name) and t.id == "IMPORTANCIAS" for t in n.targets))
        for valores, esperado in [(None, []), ({"amount": 1.0}, [{"variavel": "amount", "importancia": 1.0}])]:
            ambiente = {"MODELO": {"importancias": valores}}
            exec(compile(ast.Module(body=[atribuicao], type_ignores=[]), str(arquivo), "exec"), ambiente)
            self.assertEqual(ambiente["IMPORTANCIAS"], esperado)


if __name__ == "__main__":
    unittest.main()
