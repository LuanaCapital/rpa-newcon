import os
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

CUSTOM_FIELD_COTA = 533230
CUSTOM_FIELD_GRUPO = 533231
CUSTOM_FIELD_MES_VENCIMENTO = 731062


def buscar_oportunidade_elegivel(
    grupo: int,
    cota: int,
    mes_payload: int,
    pipeline_id: int,
    stage_id: int,
) -> int | None:
    credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if credentials_path:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path

    client = bigquery.Client()

    query = """
    SELECT
        o.id AS deal_id
    FROM `warehouse-428914.capital_piperun.piperun_oportunidades` o
    JOIN `warehouse-428914.capital_piperun.piperun_oportunidadesCamposPersonalizados` grp
        ON o.id = grp.deal_id
    JOIN `warehouse-428914.capital_piperun.piperun_oportunidadesCamposPersonalizados` cta
        ON o.id = cta.deal_id
    JOIN `warehouse-428914.capital_piperun.piperun_oportunidadesCamposPersonalizados` venc
        ON o.id = venc.deal_id
    WHERE
        o.status = 0
        AND o.pipeline_id = @pipeline_id
        AND o.stage_id = @stage_id

        AND grp.custom_field_id = @custom_field_grupo
        AND cta.custom_field_id = @custom_field_cota
        AND venc.custom_field_id = @custom_field_mes

        AND SAFE_CAST(REGEXP_REPLACE(grp.custom_field_value, r'[^0-9]', '') AS INT64) = @grupo
        AND SAFE_CAST(REGEXP_REPLACE(cta.custom_field_value, r'[^0-9]', '') AS INT64) = @cota
        AND EXTRACT(
            MONTH FROM SAFE.PARSE_DATE('%d/%m/%Y', venc.custom_field_value)
        ) = @mes_payload

    ORDER BY o.id DESC
    LIMIT 1
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("pipeline_id", "INT64", pipeline_id),
            bigquery.ScalarQueryParameter("stage_id", "INT64", stage_id),
            bigquery.ScalarQueryParameter("custom_field_grupo", "INT64", CUSTOM_FIELD_GRUPO),
            bigquery.ScalarQueryParameter("custom_field_cota", "INT64", CUSTOM_FIELD_COTA),
            bigquery.ScalarQueryParameter("custom_field_mes", "INT64", CUSTOM_FIELD_MES_VENCIMENTO),
            bigquery.ScalarQueryParameter("grupo", "INT64", grupo),
            bigquery.ScalarQueryParameter("cota", "INT64", cota),
            bigquery.ScalarQueryParameter("mes_payload", "INT64", mes_payload),
        ]
    )

    result = list(client.query(query, job_config=job_config).result())

    if not result:
        return None

    return int(result[0]["deal_id"])