# ADR 0001 - Delta Live Tables em vez de jobs Spark orquestrados à mão

**Status:** aceito

## Contexto
O medalhão poderia ser implementado como jobs PySpark agendados (como no
repositório de-lakehouse-bcb, que usa Airflow). Aqui a escolha foi DLT.

## Decisão
Delta Live Tables com Auto Loader na ingestão e expectations como quality gate.

## Justificativa
- Expectations são Data Quality declarativo com métrica automática no event
  log: o que em pipeline manual exige framework próprio, aqui é um decorator.
- Auto Loader resolve descoberta incremental de arquivos e evolução de schema
  sem código de controle de estado.
- O DLT gerencia dependência entre tabelas, retry e checkpoint; a DAG deixa de
  ser responsabilidade do autor.
- Deploy reprodutível via Asset Bundles, inclusive no Free Edition serverless.

## Consequências
- Acoplamento ao runtime Databricks: os módulos em src/dlt não rodam fora dele.
  Por isso o cliente de ingestão é Python puro e testável localmente.
- Menos controle fino de tuning do que job Spark dedicado; irrelevante no
  volume trimestral da ANS.
