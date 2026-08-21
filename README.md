# LM TECH CRM

CRM Flask + PostgreSQL preparado para Render.

## Correções desta versão
- `requests` declarado explicitamente para Authlib/Google OAuth.
- Banco inicializado automaticamente ao importar `app.py`, inclusive com Start Command simples `gunicorn app:app`.
- Retry de conexão com PostgreSQL.
- `verify_dependencies.py` faz o build falhar cedo se faltar pacote essencial.
- Python 3.12.11 configurado por `.python-version` e `render.yaml`.
- 70 leads iniciais preservados em `seeds/leads.json`.

Veja `RENDER-DEPLOY.md`.
