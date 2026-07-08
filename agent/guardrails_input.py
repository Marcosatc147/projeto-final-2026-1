"""Guardrails de entrada: validação estrutural fica no Pydantic (schema.py).

Este módulo cobre o que o Pydantic sozinho não cobre: mensagens amigáveis
(sem stack trace cru) e regras de negócio que não são erro de schema.
"""
from pydantic import ValidationError


class InputRejected(Exception):
    def __init__(self, reason: str):
        self.reason = reason
        super().__init__(reason)


def friendly_validation_error(exc: ValidationError) -> str:
    """Traduz um pydantic ValidationError em mensagem amigável, sem stack trace."""
    problems = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        problems.append(f"{field}: {error['msg']}")
    return "Dados do cliente inválidos: " + "; ".join(problems)
