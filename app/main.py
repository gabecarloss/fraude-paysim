"""Servidor da aplicação web.

Uso: uvicorn app.main:app --reload
"""

from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from src.config import ROOT

STATIC_DIR = ROOT / "app" / "static"

app = FastAPI(title="Detecção de Fraudes - PaySim")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class Transacao(BaseModel):
    type: Literal["TRANSFER", "CASH_OUT"]
    amount: float = Field(gt=0)
    hour: int = Field(ge=0, le=23)


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(transacao: Transacao):
    # TODO: carregar o modelo com joblib e devolver classe, probabilidade e importâncias
    raise HTTPException(status_code=503, detail="Modelo ainda não treinado")
