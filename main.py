from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from rpa import run_fluxo_newcon, run_lote

app = FastAPI(title="RPA Newcon")

class ClienteItem(BaseModel):
    grupo: str
    cota: str


class NewconLoteRequest(BaseModel):
    analysis_month: int = Field(..., ge=1, le=12, description="Mês de análise (1-12)")
    analysis_year: int = Field(..., ge=2000, le=2100, description="Ano de análise (ex: 2026)")
    clientes: List[ClienteItem]

@app.post("/login-newcon")
async def login_newcon(cota: str, grupo: str):
    try:
        return await run_fluxo_newcon(cota=cota, grupo=grupo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/newcon/lote")
async def newcon_lote(payload: NewconLoteRequest):
    try:
        return await run_lote(
            [c.model_dump() for c in payload.clientes],
            analysis_month=payload.analysis_month,
            analysis_year=payload.analysis_year,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))