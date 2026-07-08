"""Guardrails de saída: valida a resposta do LLM antes de devolvê-la ao usuário."""

MIN_EXPLANATION_LENGTH = 20
BOILERPLATE_PHRASES = ["não posso ajudar", "desculpe, não", "como um modelo de linguagem"]

LOW_RISK_CONTRADICTION_KEYWORDS = ["cancelar", "retenção urgente", "alto risco"]
HIGH_RISK_CONTRADICTION_KEYWORDS = ["sem ação necessária", "cliente satisfeito", "sem risco"]


def _factors_overlap(fatores_citados: list[str], fatores_reais: list[str]) -> bool:
    if not fatores_citados:
        return False
    reais_lower = " ".join(f.lower() for f in fatores_reais)
    return any(fc.lower().split(" = ")[0].split(":")[0].strip() in reais_lower for fc in fatores_citados)


def validate_llm_output(data: dict, probabilidade: float, fatores_reais: list[str]) -> tuple[bool, str]:
    """Retorna (valido, motivo_rejeicao)."""
    explicacao = data.get("explicacao", "")
    fatores_citados = data.get("fatores_citados", [])
    acao_sugerida = data.get("acao_sugerida", "")

    if len(explicacao) < MIN_EXPLANATION_LENGTH:
        return False, "explicacao_muito_curta"

    explicacao_lower = explicacao.lower()
    if any(phrase in explicacao_lower for phrase in BOILERPLATE_PHRASES):
        return False, "resposta_boilerplate"

    if not acao_sugerida:
        return False, "acao_sugerida_ausente"

    texto_completo = (explicacao_lower + " " + acao_sugerida.lower())
    if probabilidade < 0.3 and any(kw in texto_completo for kw in LOW_RISK_CONTRADICTION_KEYWORDS):
        return False, "contradicao_risco_baixo"
    if probabilidade > 0.6 and any(kw in texto_completo for kw in HIGH_RISK_CONTRADICTION_KEYWORDS):
        return False, "contradicao_risco_alto"

    if not _factors_overlap(fatores_citados, fatores_reais):
        return False, "fatores_nao_batem_alucinacao"

    return True, ""
