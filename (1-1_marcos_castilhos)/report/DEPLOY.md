# Guia de Deploy — Render (API) + Streamlit Community Cloud (dashboard)

Repositório: `https://github.com/Marcosatc147/projeto-final-2026-1`
Pasta do projeto dentro do repo: `(1-1_marcos_castilhos)/`

## 1. Deploy da API no Render

1. Acesse [render.com](https://render.com) e faça login com sua conta GitHub.
2. **New +** → **Web Service**.
3. Conecte o repositório `Marcosatc147/projeto-final-2026-1`.
4. Configurações:
   - **Root Directory:** `(1-1_marcos_castilhos)`
   - **Environment:** `Docker`
   - **Dockerfile Path:** `api/Dockerfile`
   - **Docker Build Context Directory:** `.` (relativo ao Root Directory acima)
   - **Instance Type:** Free
5. Em **Environment Variables**, adicione:
   - `GEMINI_API_KEY` = sua chave do Google AI Studio
   - `KAGGLEHUB_API_TOKEN` = seu token Kaggle (necessário para `GET /customers/sample`)
6. **Create Web Service**. Aguarde o build (leva alguns minutos na primeira vez).
7. Anote a URL pública gerada (ex: `https://churn-agent-api.onrender.com`).
8. Teste: `curl https://<sua-url>.onrender.com/health` deve retornar `{"status":"ok",...}`.

> **Nota:** o tier gratuito do Render "dorme" após 15 min de inatividade — a primeira
> requisição após esse período pode demorar ~30-60s (cold start). Mencionar isso na
> seção de UX do relatório.

## 2. Deploy do Dashboard no Streamlit Community Cloud

1. Acesse [share.streamlit.io](https://share.streamlit.io) e faça login com GitHub.
2. **New app** → selecione o repositório `Marcosatc147/projeto-final-2026-1`.
3. Configurações:
   - **Branch:** `main`
   - **Main file path:** `(1-1_marcos_castilhos)/dashboard/app.py`
4. Em **Advanced settings → Secrets**, adicione (formato TOML):
   ```toml
   API_URL = "https://<sua-url-do-render>.onrender.com"
   ```
5. **Deploy**. Aguarde o build.
6. Anote a URL pública gerada (ex: `https://churn-agent.streamlit.app`).

## 3. Após o deploy

- Atualizar o cabeçalho do `RELATORIO.md` com os dois links (API e dashboard).
- Testar o fluxo completo na URL pública antes de gravar o vídeo de demonstração.
- Se o Render "dormir" durante a demo, aguardar o cold start ou fazer um request de
  aquecimento (`curl .../health`) alguns minutos antes de gravar.
