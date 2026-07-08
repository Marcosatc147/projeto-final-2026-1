"""Fallback determinístico (sem chamada de rede) quando o LLM falha ou é rejeitado."""

ACTION_TEMPLATES = {
    "alto": "Oferecer desconto ou upgrade de plano e agendar contato proativo do time de retenção.",
    "médio": "Enviar oferta de fidelização e monitorar o cliente nos próximos ciclos de cobrança.",
    "baixo": "Nenhuma ação de retenção necessária no momento; manter monitoramento padrão.",
}


def _risk_level(probabilidade: float) -> str:
    if probabilidade > 0.6:
        return "alto"
    if probabilidade > 0.3:
        return "médio"
    return "baixo"


def template_fallback(probabilidade: float, top_fatores) -> dict:
    nivel = _risk_level(probabilidade)
    fatores_texto = ", ".join(f"{f.nome} ({f.direcao})" for f in top_fatores[:3])
    return {
        "explicacao": (
            f"[Resposta automática] Risco {nivel} de cancelamento ({probabilidade:.0%}). "
            f"Principais fatores identificados pelo modelo: {fatores_texto}."
        ),
        "fatores_citados": [f.nome for f in top_fatores[:3]],
        "acao_sugerida": ACTION_TEMPLATES[nivel],
        "fallback_used": True,
    }
