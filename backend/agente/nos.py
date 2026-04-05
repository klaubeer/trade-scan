import json
import anthropic
from backend.config import ANTHROPIC_API_KEY
from backend.schemas.modelos import SetupParams
from backend.agente.guardrails import validar_output, sanitizar_input_usuario

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM_BACKTESTER = """Você é um analista de backtesting para day traders brasileiros.

REGRAS OBRIGATÓRIAS:
1. NUNCA afirme que um setup "vai funcionar" ou "vai dar lucro" no futuro
2. SEMPRE use linguagem histórica: "nos dados testados", "no período analisado"
3. SEMPRE mencione limitações estatísticas quando total_trades < 30
4. SEMPRE alerte sobre risco de overfitting quando múltiplas variações são testadas
5. NUNCA recomende operar com dinheiro real baseado apenas no backtest

Responda em português brasileiro, direto e objetivo."""


def parse_intent(descricao: str) -> dict:
    """Extrai intenção estruturada de texto livre."""
    descricao = sanitizar_input_usuario(descricao)

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_BACKTESTER,
        messages=[{
            "role": "user",
            "content": f"""Analise esta descrição de setup de day trade e extraia as intenções em JSON:

"{descricao}"

Retorne APENAS um JSON com esta estrutura (omita campos não mencionados):
{{
  "ticker": "WIN|WDO|BITFUT",
  "timeframe": "1min|5min|15min|60min",
  "direcao": "long|short|ambos",
  "tipo_entrada": "fechamento_gatilho|rompimento_maxima|rompimento_minima|rompimento_fechamento",
  "stop_pts": número,
  "alvo_pts": número,
  "range_candle_min": número_ou_null,
  "mm200_posicao": "acima|abaixo|null",
  "mme9_posicao": "acima|abaixo|null",
  "ifr2_max": número_ou_null,
  "tendencia_semanal": "alta|baixa|lateral|qualquer|null",
  "resumo": "uma frase descrevendo o setup identificado"
}}"""
        }]
    )

    texto = resp.content[0].text.strip()
    # Extrair JSON do texto
    inicio = texto.find('{')
    fim = texto.rfind('}') + 1
    return json.loads(texto[inicio:fim])


def formulate_setup(intencao: dict, nome: str = "Setup via IA") -> SetupParams | None:
    """Converte intenção em SetupParams validado."""
    defaults = {
        "nome": nome,
        "ticker": "WIN",
        "timeframe": "5min",
        "direcao": "long",
        "tipo_entrada": "fechamento_gatilho",
        "stop_pts": 30,
        "alvo_pts": 60,
    }
    dados = {**defaults, **{k: v for k, v in intencao.items() if v and k != "resumo"}}

    # Limpar nulls explícitos
    for k in list(dados.keys()):
        if dados[k] in (None, "null", ""):
            del dados[k]

    try:
        return SetupParams(**dados)
    except Exception:
        return None


def interpret_results(stats: dict, total_trades: int) -> str:
    """Interpreta resultados do backtest com guardrails."""
    prompt = f"""Analise estes resultados de backtest e forneça uma interpretação objetiva:

{json.dumps(stats, indent=2, ensure_ascii=False)}

Inclua:
1. Avaliação geral da expectância e win rate
2. Análise do fator de lucro e drawdown
3. Padrões nas segmentações por contexto (tendência semanal, período do dia)
4. Limitações e avisos relevantes

{"AVISO OBRIGATÓRIO: mencione que com apenas " + str(total_trades) + " trades, os resultados têm baixa significância estatística." if total_trades < 30 else ""}"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        system=SYSTEM_BACKTESTER,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = resp.content[0].text
    valido, frase = validar_output(texto)
    if not valido:
        # Substituir frase problemática
        texto = texto.replace(frase, "[afirmação removida pelos guardrails]")

    return texto


def suggest_refinements(stats: dict, setup: SetupParams) -> list[dict]:
    """Sugere até 3 variações de parâmetros do setup."""
    prompt = f"""Com base nestes resultados de backtest, sugira até 3 variações de parâmetros para testar:

Setup atual: stop={setup.stop_pts}pts, alvo={setup.alvo_pts}pts, tipo={setup.tipo_entrada}
Win rate: {stats.get('win_rate')}%, Expectância: {stats.get('expectancia_pts')}pts
Segmentação: {json.dumps(stats.get('segmentacao', {}), ensure_ascii=False)}

Retorne APENAS um JSON array com até 3 objetos, cada um com os campos modificados do SetupParams:
[{{"stop_pts": X, "alvo_pts": Y, "justificativa": "..."}}]"""

    resp = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=SYSTEM_BACKTESTER,
        messages=[{"role": "user", "content": prompt}]
    )

    texto = resp.content[0].text.strip()
    inicio = texto.find('[')
    fim = texto.rfind(']') + 1
    if inicio == -1:
        return []
    try:
        sugestoes = json.loads(texto[inicio:fim])
        return sugestoes[:3]
    except Exception:
        return []
