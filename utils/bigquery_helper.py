from google.cloud import bigquery


def pode_atualizar_oportunidade(deal_id: int, mes_payload: int) -> bool:
    client = bigquery.Client()

    query = """
    SELECT 
        o.status,
        EXTRACT(MONTH FROM SAFE.PARSE_DATE('%d/%m/%Y', c.custom_field_value)) AS mes
    FROM `warehouse-428914.capital_piperun.piperun_oportunidades` o
    JOIN `warehouse-428914.capital_piperun.piperun_oportunidadesCamposPersonalizados` c
        ON o.id = c.deal_id
    WHERE 
        o.id = @deal_id
        AND c.custom_field_id = 731062
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("deal_id", "INT64", deal_id),
        ]
    )

    result = list(client.query(query, job_config=job_config).result())

    if not result:
        return False

    row = result[0]

    status = int(row["status"])
    mes = int(row["mes"]) if row["mes"] is not None else None

    if mes is None:
        return False

    return status == 0 and mes == mes_payload