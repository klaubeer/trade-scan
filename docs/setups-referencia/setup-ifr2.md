# Setup de Referência — IFR2 (Stormer / Larry Connors)

**Origem:** Larry Connors (EUA), popularizado no Brasil por Stormer
**Popularidade BR:** Alta — um dos setups mais backtestados da comunidade brasileira
**Tipo:** Reversão à média por sobrevendido/sobrecomprado

---

## Descrição

Usa o RSI de 2 períodos (IFR2) como oscilador de curtíssimo prazo. Quando o IFR2 cai abaixo de 5 (extremo sobrevendido), o preço tende a reverter para cima. Quando sobe acima de 95 (extremo sobrecomprado), tende a cair.

Diferente do RSI tradicional (14 períodos), o IFR2 é muito mais sensível e gera sinais dentro do mesmo pregão — adequado para day trade.

## Regras — IFR2 Long (Day Trade)

**Condições de entrada:**
- IFR(2) fecha abaixo de **5** no timeframe operacional

**Entrada:** abertura do candle seguinte ao sinal (ou rompimento da máxima do candle sinal)

**Stop:** mínima do candle sinal (ou fixo ~30 pts no WIN)

**Alvo (opções):**
- Máxima dos últimos 3 candles
- IFR(2) > 60 (saída dinâmica)
- Fixo ~50 pts
- Stop de tempo: encerrar após 7 candles sem atingir alvo

**Timeframe usual:** 15min, 30min

## Regras — IFR2 Short

**Condições:** IFR(2) fecha **acima de 95**
**Entrada:** abertura do candle seguinte
**Stop e alvo:** espelho do Long

## Parâmetros para TradeScan

```json
{
  "nome": "IFR2 Long - WIN 15min",
  "ticker": "WIN",
  "timeframe": "15min",
  "direcao": "long",
  "tipo_entrada": "fechamento_gatilho",
  "stop_pts": 30,
  "alvo_pts": 50,
  "horario_inicio": "09:00",
  "horario_fim": "17:00",
  "max_entradas_dia": 1
}
```

> **Nota:** Requer IFR(2) nos indicadores calculados. Adicionar junto com MME9 na lista de indicadores suportados.

## Adaptação de parâmetros para TradeScan

O PRD lista como condições de entrada: fechamento acima/abaixo da MM200, range do candle, pavio, etc. Para suportar IFR2 e 9.1, será necessário adicionar:

| Indicador | Uso |
|---|---|
| MME9 (EMA de 9 períodos) | Setup 9.1 — condição: fechar acima/abaixo da MME9 |
| IFR(2) (RSI 2 períodos) | Setup IFR2 — condição: IFR < X ou IFR > X |

Esses dois indicadores devem ser incluídos no módulo `indicadores/calculos.py` e nos parâmetros do `SetupParams`.

## Referências

- [IFR2 — Frequência do Mercado (ebook)](https://smarttbot.com/wp-content/uploads/2020/07/Ebook-IFR2.pdf)
- [Backtests IFR2 — No Alvo](https://noalvo.com/artigo/backtests-com-setup-ifr2)
