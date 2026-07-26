"""Camada bronze em Delta Live Tables: ingestão com Auto Loader.

O Auto Loader (cloudFiles) descobre arquivos novos de forma incremental,
sem relistar o diretório inteiro: é o padrão para landing zone em Databricks.
Bronze não aplica regra de negócio; apenas anexa metadados técnicos.
"""

from pyspark.sql import functions as F

import dlt  # noqa: F401 - resolvido pelo runtime do Databricks

LANDING = spark.conf.get("ans.landing_path", "/Volumes/ans/landing/demonstracoes")  # noqa: F821


@dlt.table(
    name="bronze_demonstracoes_contabeis",
    comment="Demonstrações contábeis da ANS como recebidas, uma linha por conta.",
    table_properties={"quality": "bronze", "pipelines.reset.allowed": "false"},
)
def bronze_demonstracoes_contabeis():
    return (
        spark.readStream.format("cloudFiles")  # noqa: F821
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.inferColumnTypes", "false")
        .option("cloudFiles.schemaLocation", f"{LANDING}/_schemas/demonstracoes")
        .option("delimiter", ";")
        .option("encoding", "latin1")
        .option("header", "true")
        .load(LANDING)
        .select(
            "*",
            F.col("_metadata.file_path").alias("_arquivo_origem"),
            F.current_timestamp().alias("_ingested_at"),
        )
    )
