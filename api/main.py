"""FastAPI app: monta rotas e middlewares do agente de churn."""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.logging_middleware import RequestTimingMiddleware
from api.routers import predict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("churn_agent")

app = FastAPI(
    title="Agente de Previsão de Churn",
    description="API que expõe o agente (classificador + LLM) da Trilha 1.1",
    version="1.0.0",
)

app.add_middleware(RequestTimingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Erro não tratado ao processar %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Ocorreu um erro interno ao processar sua solicitação. Tente novamente."},
    )
