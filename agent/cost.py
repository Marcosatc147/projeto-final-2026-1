"""Estimativa de custo por chamada ao Gemini 3.1 Flash Lite.

ATENÇÃO: o Gemini 3.1 Flash Lite é um modelo muito recente (lançamento
posterior ao conhecimento do assistente) e a API do Google não expõe preço
via metadata (`client.models.get`). Os valores abaixo replicam a faixa de
preço historicamente praticada pela linha "Flash-Lite" do Google (a mais
barata do catálogo Gemini) e servem como estimativa até confirmação manual
em https://ai.google.dev/gemini-api/docs/pricing — ajustar se necessário.
"""

MODEL_NAME = "gemini-3.1-flash-lite"
PRICE_INPUT_PER_MTOK_USD = 0.10
PRICE_OUTPUT_PER_MTOK_USD = 0.40


def estimate_cost_usd(input_tokens: int, output_tokens: int) -> float:
    cost = (input_tokens / 1_000_000) * PRICE_INPUT_PER_MTOK_USD
    cost += (output_tokens / 1_000_000) * PRICE_OUTPUT_PER_MTOK_USD
    return round(cost, 6)
