"""Servidor da aplicação web.

Uso: uvicorn app.main:app --reload

Endpoints:
- POST /predict: analisa uma transação (type, amount, hour) e guarda o resultado no SQLite;
- GET /historico: últimas análises guardadas;
- GET /: interface (app/static).
"""

import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import BANCO_ANALISES, FEATURES, MODELO_APLICACAO, ROOT

STATIC_DIR = ROOT / "app" / "static"

# O modelo é carregado uma única vez, quando o servidor sobe, e não a cada requisição
# (o arquivo tem cerca de 62 MB). É o dict salvo pelo src.evaluate: pipeline, limite, importâncias.
if not MODELO_APLICACAO.exists():
    raise FileNotFoundError(f"{MODELO_APLICACAO} não encontrado. Rode antes: python -m src.evaluate")
MODELO = joblib.load(MODELO_APLICACAO)
PIPELINE = MODELO["pipeline"]
LIMITE = MODELO["limite"]

# Importâncias GLOBAIS do Random Forest (MDI): dizem quanto cada variável pesou no modelo como um
# todo, e não nesta transação. Explicar cada transação exigiria outra biblioteca (ex.: SHAP).
IMPORTANCIAS = sorted(
    ({"variavel": v, "importancia": round(i, 4)} for v, i in MODELO["importancias"].items()),
    key=lambda item: item["importancia"],
    reverse=True,
)

app = FastAPI(title="Detecção de Fraudes - PaySim")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def conectar():
    # "with conexao:" só faz o commit; o closing garante que a conexão seja fechada
    return closing(sqlite3.connect(BANCO_ANALISES))


def criar_tabela():
    with conectar() as conexao, conexao:
        conexao.execute("""
            CREATE TABLE IF NOT EXISTS analises (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                type TEXT NOT NULL,
                amount REAL NOT NULL,
                hour INTEGER NOT NULL,
                probabilidade REAL NOT NULL,
                classe INTEGER NOT NULL  -- 1 = potencial fraude, 0 = legítima (como em isFraud)
            )
        """)


criar_tabela()


class Transacao(BaseModel):
    # Entradas inválidas (hora 25, valor negativo, outro tipo) recebem erro 422 do próprio
    # FastAPI, antes de chegar ao modelo e ao banco.
    type: Literal["TRANSFER", "CASH_OUT"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    hour: int = Field(ge=0, le=23)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(transacao: Transacao):
    entrada = pd.DataFrame([transacao.model_dump()])[FEATURES]
    probabilidade = float(PIPELINE.predict_proba(entrada)[0, 1])
    # Mesma convenção da Etapa 2: fraude se a probabilidade for >= limite escolhido na validação
    classe = int(probabilidade >= LIMITE)

    with conectar() as conexao, conexao:
        conexao.execute(
            "INSERT INTO analises (data_hora, type, amount, hour, probabilidade, classe) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (datetime.now().isoformat(sep=" ", timespec="seconds"),
             transacao.type, transacao.amount, transacao.hour, probabilidade, classe),
        )

    return {
        "classe": classe,
        "rotulo": "potencial fraude" if classe else "legítima",
        # O class_weight infla essa probabilidade: ela é um escore do modelo, não a chance real de fraude
        "probabilidade": probabilidade,
        "limite": LIMITE,
        "modelo": MODELO["nome"],
        "importancias": IMPORTANCIAS,
    }


@app.get("/historico")
def historico(quantidade: int = Query(10, ge=1, le=100)):
    with conectar() as conexao:
        conexao.row_factory = sqlite3.Row  # permite devolver cada linha como dict
        linhas = conexao.execute(
            "SELECT * FROM analises ORDER BY id DESC LIMIT ?", (quantidade,)
        ).fetchall()
    return [dict(linha) for linha in linhas]
