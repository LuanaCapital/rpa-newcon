from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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

@app.post("/newcon/lote")
async def newcon_lote(clientes: List[ClienteItem]):
    try:
        result = await run_lote([c.model_dump() for c in clientes])
        # se você realmente só quer ok/erro:
        return {"ok": True}
        # (se quiser o caminho do CSV: return result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))