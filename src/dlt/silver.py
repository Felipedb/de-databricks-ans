"""Camada silver: tipagem, normalização e Data Quality com expectations.

As expectations do DLT são o quality gate nativo do Databricks:
  - expect_all_or_drop descarta a linha ruim e registra a métrica;
  - expect_or_fail derruba o update inteiro em violação de contrato.
As métricas ficam no event log do pipeline, consultáveis em SQL.
"""

import dlt  # noqa: F401
from pyspark.sql import functions as F

REGRAS_DESCARTE = {
    "registro_ans_valido": "registro_ans IS NOT NULL AND registro_ans RLIKE '^[0-9]+$'",
    "conta_contabil_presente": "cd_conta_contabil IS NOT NULL",
    "valor_numerico": "vl_saldo_final IS NOT NULL",
}


@dlt.table(
    name="silver_demonstracoes_contabeis",
    comment="Demonstrações tipadas e deduplicadas. Grão: operadora x conta x competência.",
    table_properties={"quality": "silver", "delta.enableChangeDataFeed": "true"},
)
@dlt.expect_all_or_drop(REGRAS_DESCARTE)
@dlt.expect_or_fail(
    "competencia_plausivel",
    "data_competencia >= '2010-01-01' AND data_competencia <= current_date()",
)
def silver_demonstracoes_contabeis():
    bronze = dlt.read_stream("bronze_demonstracoes_contabeis")
    return (
        bronze.select(
            F.col("REG_ANS").cast("string").alias("registro_ans"),
            F.to_date(F.col("DATA"), "yyyy-MM-dd").alias("data_competencia"),
            F.col("CD_CONTA_CONTABIL").cast("string").alias("cd_conta_contabil"),
            F.col("DESCRICAO").alias("descricao_conta"),
            F.regexp_replace(F.col("VL_SALDO_FINAL"), ",", ".")
            .cast("decimal(18,2)")
            .alias("vl_saldo_final"),
            F.col("_arquivo_origem"),
            F.col("_ingested_at"),
        )
        .dropDuplicates(["registro_ans", "cd_conta_contabil", "data_competencia"])
    )
