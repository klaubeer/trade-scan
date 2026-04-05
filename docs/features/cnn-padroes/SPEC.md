# SPEC — CNN 1D para Reconhecimento de Padrões

## O que faz

Módulo de machine learning que usa CNN 1D para aprender padrões de price action a partir de trades rotulados (gain=1 / loss=0 do backtester). Funciona como filtro complementar: só confirma um trade se a CNN concordar.

## Status atual

✅ DONE

## Subtarefas

| ID | Descrição | Status | DoD |
|----|-----------|--------|-----|
| F9-001 | Tabelas DuckDB `ml_models` e `rotulos` | ✅ DONE | Schema criado em `banco/schema.py` |
| F9-002 | requirements.txt: torch, scikit-learn | ✅ DONE | Dependências adicionadas |
| F9-003 | `padroes/pipeline.py`: janelas + normalização | ✅ DONE | Sem lookahead, z-score por janela |
| F9-004 | `padroes/rotulos.py`: labeling automático | ✅ DONE | `rotular_por_run(run_id)` popula tabela `rotulos` |
| F9-005 | `padroes/modelo.py`: PatternCNN | ✅ DONE | Forward pass (1,10,50) → logits (1,2) |
| F9-006 | `padroes/treino.py`: loop + early stopping + persistência | ✅ DONE | Salva em `models/{uuid}/` + DuckDB |
| F9-007 | `padroes/inferencia.py`: predict_proba com cache LRU | ✅ DONE | `prever(model_id, ticker, tf, dt)` → float |
| F9-008 | API endpoints CNN | ✅ DONE | 5 endpoints em `main.py` |
| F9-009 | Filtro CNN no motor de backtesting | ✅ DONE | `BacktestRequest` aceita `cnn_modelo_id` + `cnn_threshold` |
| F9-010 | `CNNPadroes.jsx`: tela de treino + modelos | ✅ DONE | Formulário, métricas, loss curve, lista de modelos |
| F9-011 | `Backtesting.jsx`: checkbox + model selector + slider | ✅ DONE | Campo opcional, backward compatible |
| F9-012 | `App.jsx`: rota `/cnn-padroes` + nav | ✅ DONE | Página acessível via menu lateral |

## Decisões específicas desta feature

- **Normalização por janela**: z-score calculado apenas sobre os `seq_len` candles da janela — evita lookahead bias
- **Split temporal estrito**: nunca shuffle; 70/15/15 por ordem cronológica
- **Weighted CrossEntropyLoss**: pesos inversamente proporcionais à frequência de classe (trades de gain são minoria)
- **Import lazy de torch em motor.py**: `from backend.padroes.inferencia import prever` dentro do loop — torch só é importado se CNN estiver ativo
- **Cache LRU (maxsize=8)**: modelo não é recarregado a cada candle durante o backtesting
- **CNN não conta como slot diário**: trade filtrado pela CNN não incrementa `entradas_hoje`

## Features de entrada (n_features = 10)

`open, high, low, close, volume_fin, mm200, mme9, ifr2, range_acumulado_pct, range_candle`

## Dependências externas

- PyTorch >= 2.0 (CPU only, sem GPU)
- scikit-learn >= 1.3 (métricas: precision, recall, F1)
