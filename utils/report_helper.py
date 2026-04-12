import json
import os
from typing import Dict, Any

REPORTS_DIR = "reports"


def _get_file_path(execution_id: str) -> str:
    return os.path.join(REPORTS_DIR, f"{execution_id}.json")


def salvar_resultado(execution_id: str, resultado: dict) -> None:
    os.makedirs(REPORTS_DIR, exist_ok=True)

    path = _get_file_path(execution_id)

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            dados = json.load(f)
    else:
        dados = []

    if any(
        d.get("deal_id") == resultado.get("deal_id")
        and d.get("cota") == resultado.get("cota")
        for d in dados
    ):
        return

    dados.append(resultado)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=2, ensure_ascii=False)


def gerar_resumo(execution_id: str) -> Dict[str, Any]:
    path = _get_file_path(execution_id)

    if not os.path.exists(path):
        return {"execution_id": execution_id, "total": 0}

    with open(path, "r", encoding="utf-8") as f:
        dados = json.load(f)

    return {
        "execution_id": execution_id,
        "total": len(dados),
        "updated": sum(1 for d in dados if d.get("updated")),
        "skipped": sum(1 for d in dados if not d.get("updated")),
    }