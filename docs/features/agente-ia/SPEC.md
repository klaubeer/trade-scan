# SPEC — Agente de IA (LangGraph)

## O que faz
Permite ao usuário descrever um setup em linguagem natural. O agente formula os parâmetros, executa o backtesting como tool call e retorna interpretação dos resultados com sugestões de refinamento. Também interpreta resultados de runs já existentes.

## Status atual
📋 PLANNED

## Subtarefas

| ID | Descrição | Status | DoD |
|----|-----------|--------|-----|
| F6-001 | Estrutura do grafo LangGraph | 📋 PLANNED | Grafo compila, nós definidos |
| F6-002 | Nó `parse_intent` | 📋 PLANNED | Extrai intenção de 3 textos de teste |
| F6-003 | Nó `formulate_setup` | 📋 PLANNED | Output validado Pydantic antes de prosseguir |
| F6-004 | Nó `run_backtest` (tool call) | 📋 PLANNED | Chama motor e passa resultado |
| F6-005 | Nó `interpret_results` + guardrails | 📋 PLANNED | Checklist de guardrails no código |
| F6-006 | Nó `suggest_refinements` | 📋 PLANNED | Retorna ≤3 variações como SetupParams |
| F6-007 | Rota SSE `/api/agente/explorar` | 📋 PLANNED | Frontend recebe steps em tempo real |
| F6-008 | Rota `/api/agente/interpretar` | 📋 PLANNED | Interpretação de run existente |
| F6-009 | Frontend — chat modo exploração | 📋 PLANNED | Steps exibidos conforme chegam |

## Decisões específicas desta feature

- **Streaming via SSE** — cada nó do grafo emite um evento SSE com seu output parcial. Frontend exibe progressivamente: "Interpretando setup...", "Executando backtest...", "Analisando resultados..."
- **Validação Pydantic antes de executar** — se o LLM gerar `SetupParams` inválido (ex: `stop_pts` negativo), o grafo vai para nó `pedir_esclarecimento` ao invés de tentar executar
- **Guardrails implementados no código** — não apenas no system prompt. O nó `interpret_results` tem checklist explícito que verifica se o output contém frases proibidas antes de retornar
- **Modo interpretação é stateless** — recebe `run_id`, busca dados do DuckDB, chama LLM, retorna. Sem estado de conversa.

## Grafo LangGraph

```
START
  ↓
parse_intent
  ↓
formulate_setup ──(inválido)──→ pedir_esclarecimento → END
  ↓ (válido)
run_backtest
  ↓
interpret_results
  ↓
suggest_refinements
  ↓
END
```

## System prompt — guardrails

```
Você é um analista de backtesting. Suas respostas devem:
1. NUNCA afirmar que um setup "vai funcionar" ou "é lucrativo" no futuro
2. SEMPRE usar linguagem histórica: "nos dados testados", "no período analisado"
3. SEMPRE mencionar a limitação estatística se total_trades < 30
4. SEMPRE alertar sobre overfitting se o usuário testou mais de 5 variações no mesmo período
5. NUNCA recomendar operar com dinheiro real baseado apenas no backtest

Formato de resposta: português brasileiro, direto, sem jargão excessivo.
```

## Frases proibidas (checklist no código)

```python
FRASES_PROIBIDAS = [
    "vai funcionar",
    "vai dar lucro",
    "recomendo operar",
    "setup lucrativo",
    "pode operar",
    "garante",
]

def validar_output_guardrails(texto: str) -> bool:
    texto_lower = texto.lower()
    return not any(frase in texto_lower for frase in FRASES_PROIBIDAS)
```

## Formato do evento SSE por nó

```
event: step
data: {"no": "parse_intent", "status": "concluido", "resumo": "Identificado setup de compra no rompimento com filtro de range"}

event: step
data: {"no": "formulate_setup", "status": "concluido", "setup": {...SetupParams...}}

event: step
data: {"no": "run_backtest", "status": "executando"}

event: step
data: {"no": "run_backtest", "status": "concluido", "run_id": 42, "total_trades": 87}

event: step
data: {"no": "interpret_results", "status": "concluido", "interpretacao": "..."}

event: result
data: {"run_id": 42, "interpretacao": "...", "sugestoes": [...]}
```

## Dependências externas
- LangGraph 0.3.x
- anthropic SDK 0.40.x
- FastAPI SSE (via `StreamingResponse` com `text/event-stream`)
