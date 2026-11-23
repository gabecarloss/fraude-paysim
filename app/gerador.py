"""Geração local de entradas fictícias para demonstração, sem alterar o treinamento."""

import json
from typing import Literal
from urllib.error import HTTPError, URLError
from urllib.request import ProxyHandler, Request, build_opener

from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Transacao(BaseModel):
    type: Literal["TRANSFER", "CASH_OUT"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    hour: int = Field(ge=0, le=23)


class PedidoCenario(BaseModel):
    pedido: str = Field(min_length=5, max_length=1000)
    modelo: str = Field(min_length=1, max_length=100, pattern=r"^[\w.:-]+$")


class Cenario(Transacao):
    model_config = ConfigDict(extra="forbid")
    descricao: str = Field(min_length=1, max_length=400)


def gerar_cenario(pedido: PedidoCenario):
    # Endereço fixo de loopback; não usa proxies nem serviços externos.
    # O modelo deve ter sido baixado no Ollama antes da apresentação.
    esquema = Cenario.model_json_schema()
    corpo = {
        "model": pedido.modelo,
        "stream": False,
        "format": esquema,
        "options": {"temperature": 0, "repeat_penalty": 1.2, "num_predict": 400},
        "messages": [
            {"role": "system", "content": (
                "Crie uma única transação FICTÍCIA para uma demonstração acadêmica. "
                "Responda em português e apenas no JSON solicitado. "
                "Use os tipos do PaySim: TRANSFER para transferência ou CASH_OUT para saque. "
                "O valor é meramente ilustrativo; hora deve ser inteira entre 0 e 23. "
                "Não gere pessoas, contas, documentos, rótulos de fraude, probabilidades ou "
                "garantias sobre o resultado do classificador. "
                "A descrição deve ser uma frase curta, sem números e sem moeda. "
                "Não repita palavras ou sequências numéricas. Esquema: "
                + json.dumps(esquema, ensure_ascii=False)
            )},
            {"role": "user", "content": pedido.pedido},
        ],
    }
    requisicao = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(corpo).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        # Consulta os metadados antes de enviar o cenário. Isso também identifica
        # aliases de modelos remotos que não têm "cloud" no nome.
        consulta = Request(
            "http://127.0.0.1:11434/api/show",
            data=json.dumps({"model": pedido.modelo}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with build_opener(ProxyHandler({})).open(consulta, timeout=10) as resposta:
            metadados = json.loads(resposta.read(1_000_000))
        if (metadados.get("remote_host") or metadados.get("remote_model")
                or not metadados.get("model_info")):
            raise HTTPException(status_code=422, detail=(
                "Escolha um modelo baixado localmente no Ollama. Modelos remotos não são aceitos."
            ))
        with build_opener(ProxyHandler({})).open(requisicao, timeout=90) as resposta:
            dados = json.loads(resposta.read(1_000_000))
        cenario = Cenario.model_validate_json(dados["message"]["content"])
    except HTTPError as erro:
        mensagem = ("Modelo não encontrado no Ollama. Confira o nome em ollama list."
                    if erro.code == 404 else "O Ollama recusou a geração. Confira o modelo local.")
        raise HTTPException(status_code=503, detail=mensagem) from erro
    except (URLError, TimeoutError, OSError) as erro:
        raise HTTPException(status_code=503, detail=(
            "O Ollama local não respondeu. Abra o Ollama e confira se o modelo está instalado."
        )) from erro
    except (ValueError, KeyError, TypeError, ValidationError) as erro:
        raise HTTPException(status_code=502, detail=(
            "A LLM devolveu uma entrada inválida. Tente gerar novamente."
        )) from erro
    return {"ficticio": True, "modelo_gerador": pedido.modelo, **cenario.model_dump()}
