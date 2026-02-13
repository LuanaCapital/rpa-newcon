from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rpa import run_fluxo_newcon, run_lote

app = FastAPI(title="RPA Newcon")

class ClienteItem(BaseModel):
    grupo: str
    cota: str


@app.post("/login-newcon")
async def login_newcon(cota: str, grupo: str):
    """
    Rota que dispara a RPA de login no Newcon.
    """
    try:
        result = await run_fluxo_newcon(cota=cota, grupo=grupo)
        return result
    except Exception as e:
        # Aqui você pode melhorar o tratamento de erro/log
        raise HTTPException(status_code=500, detail=str(e))

class NewconLoteRequest(BaseModel):
    analysis_month: int = Field(..., ge=1, le=12, description="Mês de análise (1-12)")
    analysis_year: int = Field(..., ge=2000, le=2100, description="Ano de análise (ex: 2026)")
    clientes: List[ClienteItem]

@app.post("/newcon/lote")
async def newcon_lote(payload: NewconLoteRequest):
    try:
        result = await run_lote(
            [c.model_dump() for c in payload.clientes],
            analysis_month=payload.analysis_month,
            analysis_year=payload.analysis_year,
        )
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))