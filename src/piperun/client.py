import os
import re
from typing import Any, Dict, List, Optional

import requests


class PipeRunAPIError(Exception):
    pass


class PipeRunClient:
    def __init__(
        self,
        token: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = 30,
    ) -> None:
        self.token = token or os.getenv("PIPERUN_TOKEN")
        self.base_url = (base_url or os.getenv("PIPERUN_BASE_URL") or "").rstrip("/")
        self.timeout = timeout

        if not self.token:
            raise ValueError("PIPERUN_TOKEN não configurado")

        if not self.base_url:
            raise ValueError("PIPERUN_BASE_URL não configurado")

    def _headers(self) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "content-type": "application/json",
            "token": self.token,
        }

    def _handle_response(self, response: requests.Response, error_prefix: str) -> Dict[str, Any]:
        if response.ok:
            try:
                return response.json()
            except ValueError:
                return {"success": True, "message": response.text}

        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text

        raise PipeRunAPIError(
            f"{error_prefix}: HTTP {response.status_code} - {error_body}"
        )

    def list_deals(self, *, cursor: str = "", show: int = 100) -> Dict[str, Any]:
        url = f"{self.base_url}/deals"
        response = requests.get(
            url,
            headers=self._headers(),
            params={"cursor": cursor, "show": show},
            timeout=self.timeout,
        )
        return self._handle_response(response, "Erro ao listar oportunidades")

    def find_open_retention_deal(
            self,
            *,
            grupo: object,
            cota: object,
            pipeline_id: int,
            stage_id: int,
    ) -> Optional[Dict[str, Any]]:
        grupo_num = str(grupo).lstrip("0")
        cota_num = str(cota).lstrip("0")

        pattern = re.compile(
            rf"\[\s*0*{re.escape(grupo_num)}\s*\]\s*-\s*0*{re.escape(cota_num)}"
        )

        cursor = ""

        while True:
            payload = self.list_deals(cursor=cursor)
            data = payload.get("data") or []

            for deal in data:
                deal_pipeline_id = (
                        deal.get("pipeline_id")
                        or deal.get("pipe_id")
                        or deal.get("funnel_id")
                )

                deal_stage_id = (
                        deal.get("stage_id")
                        or deal.get("deal_stage_id")
                        or (
                            deal.get("stage", {}).get("id")
                            if isinstance(deal.get("stage"), dict)
                            else None
                        )
                )

                if str(pipeline_id) != str(deal_pipeline_id):
                    continue

                if str(stage_id) != str(deal_stage_id):
                    continue

                status = deal.get("status")
                if str(status) not in {"0", "open", "aberto", "aberta"}:
                    continue

                title = str(deal.get("title") or "").strip()
                if not pattern.search(title):
                    continue

                return deal

            meta = payload.get("meta") or {}
            cursor_info = meta.get("cursor") or {}
            cursor = cursor_info.get("next") or ""

            if not cursor:
                break

        return None

    def update_deal(self, deal_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/deals/{int(deal_id)}"
        response = requests.put(
            url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
        )
        return self._handle_response(
            response,
            f"Erro ao atualizar oportunidade {deal_id}",
        )