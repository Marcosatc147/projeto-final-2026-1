from agent.fallback import template_fallback
from model.explain import Factor


def _fatores():
    return [
        Factor(nome="tenure", contribuicao=-1.8, direcao="reduz risco"),
        Factor(nome="Contract = Month-to-month", contribuicao=0.9, direcao="aumenta risco"),
    ]


def test_fallback_high_risk():
    result = template_fallback(0.85, _fatores())
    assert result["fallback_used"] is True
    assert "alto" in result["explicacao"]
    assert "desconto" in result["acao_sugerida"].lower()


def test_fallback_medium_risk():
    result = template_fallback(0.45, _fatores())
    assert "médio" in result["explicacao"]


def test_fallback_low_risk():
    result = template_fallback(0.1, _fatores())
    assert "baixo" in result["explicacao"]
    assert "nenhuma ação" in result["acao_sugerida"].lower()


def test_fallback_never_makes_network_calls():
    # Fallback é 100% determinístico — nenhuma dependência de rede é importada aqui.
    import agent.fallback as fallback_module
    assert "requests" not in dir(fallback_module)
    assert "google" not in dir(fallback_module)
