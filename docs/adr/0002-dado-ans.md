# ADR 0002 - Demonstrações contábeis da ANS como dataset

**Status:** aceito

## Contexto
O projeto precisava de dado público brasileiro com volume real e relevância
de domínio.

## Decisão
Demonstrações contábeis trimestrais das operadoras de saúde (dados abertos ANS).

## Justificativa
- Volume real: centenas de milhares de linhas por trimestre, anos de histórico.
- Formato sujo de verdade: latin-1, separador ';', decimal com vírgula,
  variação de layout entre anos. Ótimo para demonstrar tratamento na silver.
- Domínio regulado: conversa com governança, auditoria e LGPD.

## Consequências
- O layout pode mudar entre anos; o parsing da silver concentra essa variação.
- O padrão de URL do FTP da ANS pode mudar; está isolado em montar_url.
