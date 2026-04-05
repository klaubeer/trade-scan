FRASES_PROIBIDAS = [
    "vai funcionar",
    "vai dar lucro",
    "recomendo operar",
    "setup lucrativo",
    "pode operar",
    "garante",
    "certamente",
    "com certeza vai",
]


def validar_output(texto: str) -> tuple[bool, str | None]:
    """
    Retorna (valido, frase_encontrada).
    Se inválido, retorna a frase que violou os guardrails.
    """
    texto_lower = texto.lower()
    for frase in FRASES_PROIBIDAS:
        if frase in texto_lower:
            return False, frase
    return True, None


def sanitizar_input_usuario(texto: str) -> str:
    """Remove caracteres potencialmente problemáticos para injeção de prompt."""
    # Remove delimitadores de sistema comuns
    for token in ["<|system|>", "<|user|>", "<|assistant|>", "###", "---SYSTEM"]:
        texto = texto.replace(token, "")
    return texto[:2000]  # Limitar tamanho
