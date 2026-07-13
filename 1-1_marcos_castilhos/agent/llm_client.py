"""Wrapper fino sobre a API do Gemini para a camada de explicação do agente."""
import json
import os
import time

from google import genai
from google.genai import errors as genai_errors
from google.genai import types

from agent.cost import MODEL_NAME, estimate_cost_usd
from agent.prompts import OUTPUT_SCHEMA, SYSTEM_PROMPT, build_user_prompt

LLM_TIMEOUT_MS = 10_000

# Erros retryable/esperados do provedor — o orchestrator captura esta tupla
# para decidir cair no fallback determinístico.
LLMProviderError = (genai_errors.APIError, genai_errors.ClientError, genai_errors.ServerError)


class LLMCallResult:
    def __init__(self, data: dict, latency_ms: int, tokens_input: int, tokens_output: int):
        self.data = data
        self.latency_ms = latency_ms
        self.tokens_input = tokens_input
        self.tokens_output = tokens_output
        self.custo_estimado_usd = estimate_cost_usd(tokens_input, tokens_output)


def _client() -> genai.Client:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise genai_errors.ClientError(
            code=401, response_json={"error": {"message": "GEMINI_API_KEY não configurada"}}
        )
    return genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(timeout=LLM_TIMEOUT_MS),
    )


async def explain_churn(customer_summary: str, probabilidade: float, fatores) -> LLMCallResult:
    """Chama o Gemini para gerar explicação + ação sugerida.

    Propaga exceções do SDK (google.genai.errors.APIError e subclasses) — o
    chamador (orchestrator) decide quando cair no fallback.
    """
    client = _client()
    start = time.monotonic()

    response = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=build_user_prompt(customer_summary, probabilidade, fatores),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type="application/json",
            response_schema=OUTPUT_SCHEMA,
        ),
    )

    latency_ms = int((time.monotonic() - start) * 1000)
    data = json.loads(response.text)

    usage = response.usage_metadata
    return LLMCallResult(
        data=data,
        latency_ms=latency_ms,
        tokens_input=usage.prompt_token_count or 0,
        tokens_output=usage.candidates_token_count or 0,
    )
