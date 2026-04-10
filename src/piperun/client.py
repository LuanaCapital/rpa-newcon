from __future__ import annotations
import os
import re
from typing import Any, Dict, Optional
import requests
from utils.betterstack_logger import get_logger

logger = get_logger(__name__)


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
            logger.error("PIPERUN_TOKEN não configurado")
            raise ValueError("PIPERUN_TOKEN não configurado")

        if not self.base_url:
            logger.error("PIPERUN_BASE_URL não configurado")
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
                body = response.json()
            except ValueError:
                body = {"success": True, "message": response.text}

            logger.info(
                "Resposta recebida do PipeRun com sucesso",
                extra={
                    "event": "piperun_response_success",
                    "status_code": response.status_code,
                    "url": response.url,
                    "method": response.request.method if response.request else None,
                },
            )
            return body

        try:
            error_body = response.json()
        except ValueError:
            error_body = response.text

        logger.error(
            "Erro retornado pela API do PipeRun",
            extra={
                "event": "piperun_response_error",
                "status_code": response.status_code,
                "url": response.url,
                "method": response.request.method if response.request else None,
                "error_prefix": error_prefix,
                "error_body": error_body,
            },
        )

        raise PipeRunAPIError(
            f"{error_prefix}: HTTP {response.status_code} - {error_body}"
        )

    def list_deals(self, *, cursor: str = "", show: int = 100) -> Dict[str, Any]:
        url = f"{self.base_url}/deals"
        try:
            response = requests.get(
                url,
                headers=self._headers(),
                params={"cursor": cursor, "show": show},
                timeout=self.timeout,
            )
            return self._handle_response(response, "Erro ao listar oportunidades")
        except requests.RequestException:
            logger.exception(
                "Falha de comunicação ao listar oportunidades no PipeRun",
                extra={
                    "event": "piperun_list_deals_request_exception",
                    "url": url,
                    "cursor": cursor,
                    "show": show,
                },
            )
            raise

    def find_open_retention_deal(
            self,
            *,
            grupo: object,
            cota: object,
            pipeline_id: int,
            stage_id: int,
            max_pages: int = 50,
    ) -> Optional[Dict[str, Any]]:
        grupo_num = str(grupo).lstrip("0")
        cota_num = str(cota).lstrip("0")

        pattern = re.compile(
            rf"\[\s*0*{re.escape(grupo_num)}\s*\]\s*-\s*0*{re.escape(cota_num)}"
        )

        cursor = ""
        page_count = 0

        while page_count < max_pages:
            payload = self.list_deals(cursor=cursor)
            data = payload.get("data") or []
            page_count += 1

            logger.info(
                "Procurando deal no PipeRun",
                extra={
                    "event": "piperun_searching_deal",
                    "grupo": str(grupo),
                    "cota": str(cota),
                    "page": page_count,
                    "max_pages": max_pages,
                    "deals_nesta_pagina": len(data),
                },
            )

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

                logger.info(
                    "Oportunidade aberta encontrada no PipeRun",
                    extra={
                        "event": "piperun_open_retention_deal_found",
                        "grupo": str(grupo),
                        "cota": str(cota),
                        "pipeline_id": pipeline_id,
                        "stage_id": stage_id,
                        "deal_id": deal.get("id"),
                        "deal_title": title,
                        "deal_status": status,
                        "page": page_count,
                    },
                )

                return deal

            meta = payload.get("meta") or {}
            cursor_info = meta.get("cursor") or {}
            cursor = cursor_info.get("next") or ""

            if not cursor:
                logger.info(
                    "Fim da paginação do PipeRun",
                    extra={
                        "event": "piperun_pagination_end",
                        "grupo": str(grupo),
                        "cota": str(cota),
                        "paginas_processadas": page_count,
                    },
                )
                break

        logger.warning(
            "Nenhuma oportunidade aberta encontrada no PipeRun após buscar",
            extra={
                "event": "piperun_open_retention_deal_not_found",
                "grupo": str(grupo),
                "cota": str(cota),
                "pipeline_id": pipeline_id,
                "stage_id": stage_id,
                "paginas_buscadas": page_count,
                "max_pages": max_pages,
            },
        )

        return None

    def update_deal(self, deal_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}/deals/{int(deal_id)}"

        logger.info(
            "Atualizando oportunidade no PipeRun",
            extra={
                "event": "piperun_update_deal_start",
                "deal_id": int(deal_id),
                "url": url,
                "payload": payload,
            },
        )

        try:
            response = requests.put(
                url,
                headers=self._headers(),
                json=payload,
                timeout=self.timeout,
            )

            result = self._handle_response(
                response,
                f"Erro ao atualizar oportunidade {deal_id}",
            )

            logger.info(
                "Oportunidade atualizada com sucesso no PipeRun",
                extra={
                    "event": "piperun_update_deal_success",
                    "deal_id": int(deal_id),
                    "url": url,
                    "payload": payload,
                },
            )

            return result

        except requests.RequestException:
            logger.exception(
                "Falha de comunicação ao atualizar oportunidade no PipeRun",
                extra={
                    "event": "piperun_update_deal_request_exception",
                    "deal_id": int(deal_id),
                    "url": url,
                    "payload": payload,
                },
            )
            raise
        except Exception:
            logger.exception(
                "Erro inesperado ao atualizar oportunidade no PipeRun",
                extra={
                    "event": "piperun_update_deal_unexpected_exception",
                    "deal_id": int(deal_id),
                    "url": url,
                    "payload": payload,
                },
            )
            raise
