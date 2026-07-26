"""Camada gold: agregados analíticos por operadora e competência.

Materializada como tabela (não streaming): agregação completa recalculada a
cada update, adequado ao volume trimestral da ANS.
"""

from pyspark.sql import functions as F

import dlt  # noqa: F401

# Grupos do plano de contas da ANS usados nos indicadores.
CONTA_RECEITA = "3"
CONTA_DESPESA = "4"


@dlt.table(
    name="gold_indicadores_operadora",
    comment="Receita, despesa e resultado por operadora e competência.",
    table_properties={"quality": "gold"},
)
def gold_indicadores_operadora():
    silver = dlt.read("silver_demonstracoes_contabeis")
    return (
        silver.withColumn("grupo_conta", F.substring("cd_conta_contabil", 1, 1))
        .filter(F.col("grupo_conta").isin(CONTA_RECEITA, CONTA_DESPESA))
        .groupBy("registro_ans", "data_competencia")
        .agg(
            F.sum(
                F.when(F.col("grupo_conta") == CONTA_RECEITA, F.col("vl_saldo_final")).otherwise(0)
            ).alias("receita_total"),
            F.sum(
                F.when(F.col("grupo_conta") == CONTA_DESPESA, F.col("vl_saldo_final")).otherwise(0)
            ).alias("despesa_total"),
        )
        .withColumn("resultado", F.col("receita_total") - F.col("despesa_total"))
        .withColumn(
            "margem_pct",
            F.when(
                F.col("receita_total") != 0,
                F.round(F.col("resultado") / F.col("receita_total") * 100, 2),
            ),
        )
    )
