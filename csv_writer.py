import csv
import os
from datetime import datetime

DEFAULT_HEADERS = [
    "grupo_base",
    "cota_base",
    "em_aberto",
    "cota_pendencia",
    "vencimento",
    "valor",
    "deal_id",
    "piperun_result",
    "erro",
]

def build_csv_path(base_dir: str = "outputs") -> str:
    os.makedirs(base_dir, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return os.path.join(base_dir, f"resultado_lote_{ts}.csv")

def append_rows(csv_path: str, rows: list[dict]):
    file_exists = os.path.exists(csv_path)

    with open(csv_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=DEFAULT_HEADERS)

        if not file_exists:
            writer.writeheader()

        for r in rows:
            # garante que todas as colunas existem
            out = {h: r.get(h, "") for h in DEFAULT_HEADERS}
            writer.writerow(out)
