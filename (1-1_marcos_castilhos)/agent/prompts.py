"""Templates de prompt estruturado para a camada de explicação do agente."""

SYSTEM_PROMPT = """Você é um especialista em retenção de clientes de telecom.
Você recebe o perfil de um cliente e a saída de um modelo de ML (probabilidade
de churn + fatores mais importantes).

Sua tarefa:
1. Explicar em linguagem natural, de forma clara e factual, por que esse
   cliente está em risco — citando APENAS os fatores reais fornecidos, nunca
   inventando fatores que não estão na lista.
2. Sugerir 1-2 ações de retenção concretas e específicas para esse perfil.

Se a probabilidade for baixa (< 0.3), explique por que o cliente parece
estável em vez de sugerir retenção.

Responda em JSON estrito com os campos: explicacao, fatores_citados,
acao_sugerida."""

OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "explicacao": {"type": "string"},
        "fatores_citados": {"type": "array", "items": {"type": "string"}},
        "acao_sugerida": {"type": "string"},
    },
    "required": ["explicacao", "fatores_citados", "acao_sugerida"],
}


def build_user_prompt(customer_summary: str, probabilidade: float, fatores) -> str:
    fatores_texto = "\n".join(
        f"- {f.nome}: contribuição {f.contribuicao:+.3f} ({f.direcao})" for f in fatores
    )
    return (
        f"Cliente: {customer_summary}\n"
        f"Probabilidade de churn (modelo LogisticRegression): {probabilidade:.2%}\n"
        f"Top fatores:\n{fatores_texto}"
    )
