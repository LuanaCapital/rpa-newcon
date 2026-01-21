from __future__ import annotations
from datetime import date
import os

from src.domain.types import RPACotaStatus
from src.sheets.updater import sync_payments_to_sheet


def main():
    """
    MAIN ESTÁTICO
    - Não chama RPA
    - Usa dados mockados
    - Serve para validar:
        * autenticação Google Sheets
        * leitura da planilha
        * identificação de colunas
        * escrita no mês correto
    """

    # =========================
    # CONFIGURAÇÃO FIXA
    # =========================
    SPREADSHEET_ID = os.environ.get(
        "SHEET_ID",
        "COLOQUE_AQUI_O_SPREADSHEET_ID"
    )

    SHEET_NAME = "Página2"          # nome da aba
    READ_RANGE = "Página2!A1:ZZ"    # intervalo grande o suficiente

    # Simulando execução em 09/01/2026
    RUN_DATE = date(2026, 1, 9)

    # =========================
    # DADOS MOCKADOS (RPA FAKE)
    # =========================
    # Exemplo prático 1 + 2
    mock_results = [
        # Exemplo 1:
        # Grupo 6600 / Cota 1792
        # Janeiro 2026 estava vazio
        # Agora confirmou pagamento
        RPACotaStatus(
            grupo=6600,
            cota=1792,
            pago_confirmado=True
        ),

        # Exemplo 2:
        # Grupo 6600 / Cota 1147
        # Cliente tem outra cota (1242)
        # Nenhuma paga
        RPACotaStatus(
            grupo=6600,
            cota=1147,
            pago_confirmado=False
        ),
        RPACotaStatus(
            grupo=6600,
            cota=1242,
            pago_confirmado=False
        ),
    ]

    # =========================
    # EXECUÇÃO
    # =========================
    print("Iniciando sincronização com Google Sheets (modo estático)...")

    result = sync_payments_to_sheet(
        spreadsheet_id="1un-lnJ0vUimoyiwNjApyjygbIyEGhJKNcL4iWLiOnf8",
        sheet_name="pag2",
        read_range_a1="pag2!A1:ZZ",
        run_date=RUN_DATE,
        results=mock_results,
        token_path="../token.json",
    )

    # =========================
    # OUTPUT
    # =========================
    print("\nResumo da execução:")
    print(f" - Total de células atualizadas: {result['updated']}")

    if result["updated"] > 0:
        print("\nDetalhes:")
        for upd in result["updates"]:
            print(
                f" • {upd['range_a1']} = {upd['value']} "
                f"({upd['reason']})"
            )
    else:
        print(" - Nenhuma atualização necessária.")

    print("\nExecução finalizada.")


if __name__ == "__main__":
    main()
