import csv
import os

CSV_DIR = "relatorios"


def salvar_resultado_csv(execution_id: str, resultado: dict):
    os.makedirs(CSV_DIR, exist_ok=True)

    path = os.path.join(CSV_DIR, f"{execution_id}.csv")

    cotas = resultado.get("resultado", {}).get("cotas", [])

    existentes = set()

    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                chave = (row.get("deal_id"), row.get("cota_pendencia"))
                existentes.add(chave)

    file_exists = os.path.exists(path)

    with open(path, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=[
                "deal_id",
                "grupo",
                "cota",
                "pago",
                "cota_pendencia",
                "vencimento",
                "valor",
                "resultado",
                "piperun_result",
                "erro",
            ],
        )

        if not file_exists:
            writer.writeheader()

        for cota_item in cotas:
            chave = (
                str(resultado.get("piperun_result", {}).get("deal_id")),
                str(cota_item.get("cota")),
            )

            if chave in existentes:
                continue

            writer.writerow(
                {
                    "deal_id": resultado.get("piperun_result", {}).get("deal_id"),
                    "grupo": resultado.get("grupo"),
                    "cota": resultado.get("cota"),
                    "pago": resultado.get("pago"),
                    "cota_pendencia": cota_item.get("cota"),
                    "vencimento": cota_item.get("vencimento"),
                    "valor": cota_item.get("valor"),
                    "resultado": "Sem pendência"
                    if not cota_item.get("em_aberto")
                    else "Com pendência",
                    "piperun_result": resultado.get("piperun_result", {}).get("reason"),
                    "erro": resultado.get("erro"),
                }
            )