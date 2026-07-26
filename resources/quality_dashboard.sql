-- Métricas de Data Quality extraídas do event log do pipeline DLT.
-- Cada expectation vira linha aqui: quantas passaram, quantas caíram.
SELECT
  timestamp,
  details:flow_progress.data_quality.expectations AS expectations
FROM event_log(TABLE(ans.demonstracoes.silver_demonstracoes_contabeis))
WHERE details:flow_progress.data_quality IS NOT NULL
ORDER BY timestamp DESC;
