# Setup de Referência — ABC (Price Action)

**Origem:** Price Action clássico (sem autor único)
**Popularidade BR:** Alta — ensinado em praticamente todos os cursos de day trade nacionais
**Tipo:** Continuação de tendência / correção

---

## Descrição

Padrão de três pontos que identifica o fim de uma correção dentro de uma tendência. O preço forma um topo (A), corrige até um fundo (B) e sobe até um novo topo (C) — que fica abaixo de A. A entrada é no rompimento de C, apostando na continuação da tendência principal.

```
A         C
 \       /
  \     /
   \   /
    \ /
     B
```

## Regras — ABC Long

**Condições:**
1. Tendência de alta estabelecida (preço acima da MM200 ou primeiro candle de alta)
2. Identificar topo A → fundo B → topo C (C < A)
3. Candle gatilho fecha acima de C ou rompe a máxima de C

**Entrada:** rompimento da máxima do candle gatilho (ponto C)

**Stop:** abaixo do fundo B (ou fixo ~30 pts no WIN)

**Alvo:** projeção de AB a partir de C (AB = distância A→B; alvo = C + AB) ou fixo ~60 pts

**Timeframe usual:** 5min, 15min

## Regras — ABC Short (espelho)

Tudo invertido: fundo A → topo B → fundo C (C > A). Entrada no rompimento da mínima de C.

## Parâmetros para TradeScan

```json
{
  "nome": "ABC Long - WIN 5min",
  "ticker": "WIN",
  "timeframe": "5min",
  "direcao": "long",
  "tipo_entrada": "rompimento_maxima",
  "mm200_posicao": "acima",
  "stop_pts": 30,
  "alvo_pts": 60,
  "horario_inicio": "09:00",
  "horario_fim": "17:00",
  "max_entradas_dia": 2
}
```

> **Nota:** A identificação automática dos pontos A, B, C (swing highs/lows) requer lógica de detecção de pivot points — feature adicional além do escopo inicial do PRD. Para o backtesting inicial, simplificar como: "candle que fecha acima da MME9 após correção de pelo menos N pontos".

## Referências

- [Padrão ABC — Sato Trader](https://satotrader.com.br/blog/o-padrao-mais-facil-do-brasil-para-mini-indice-e-mini-dolar)
