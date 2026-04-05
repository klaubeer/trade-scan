# Setup de Referência — 9.1 de Larry Williams

**Origem:** Larry Williams (adaptado para mercado brasileiro)
**Popularidade BR:** Alta — amplamente usado em WIN e WDO
**Tipo:** Reversão à média

---

## Descrição

Setup de reversão baseado na MME9 (Média Móvel Exponencial de 9 períodos). Identifica momentos em que o preço se afastou da MME9 e busca capturar o retorno em direção a ela.

## Variantes

| Variante | Gatilho |
|---|---|
| 9.1 | Candle fecha abaixo da MME9 (venda) ou acima (compra) — entrada no rompimento do candle seguinte |
| 9.2 | Dois candles consecutivos abaixo/acima da MME9 |
| 9.3 | Três candles consecutivos abaixo/acima da MME9 |

## Regras — 9.1 Long (adaptação WIN 5min)

**Condições de entrada:**
- Candle fecha **abaixo** da MME9 (pull-back)
- Próximo candle rompe a **máxima** do candle anterior (confirmação de reversão)

**Entrada:** rompimento da máxima do candle gatilho

**Stop:** mínima do candle gatilho (ou fixo ~25 pts no WIN)

**Alvo:** próxima resistência relevante ou fixo ~50 pts (payoff ~2:1)

**Horário:** 09:00 às 17:00 (evitar últimos 30min)

**Timeframe usual:** 5min ou 15min

## Parâmetros para TradeScan

```json
{
  "nome": "9.1 Larry Williams Long - WIN 5min",
  "ticker": "WIN",
  "timeframe": "5min",
  "direcao": "long",
  "tipo_entrada": "rompimento_maxima",
  "stop_pts": 25,
  "alvo_pts": 50,
  "horario_inicio": "09:00",
  "horario_fim": "17:00",
  "max_entradas_dia": 2
}
```

> **Nota:** A condição de "fechar abaixo da MME9" requer adicionar suporte a MME9 nos indicadores calculados (PRD atual lista apenas MM200 simples). Incluir na implementação.

## Referências

- [Setup 9.1 — Frequência do Mercado](https://frequenciadomercado.com.br/setup-9-1-de-larry-williams/)
- [Setup 9.1 — Portal do Trader](https://portaldotrader.com.br/plano-tnt/analise-tecnica-na-pratica/setups-com-indicadores-simples/operando-setups-larry-williams-91)
