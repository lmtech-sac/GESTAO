# LM TECH CRM — Advocacia

CRM comercial com backend Flask, banco compartilhado, Google OAuth, metas, contratos, reuniões por lead e auditoria por usuário.

## Deploy recomendado: Render

O projeto já vem pronto para Render com:

- `render.yaml` na raiz;
- Web Service Python + Gunicorn;
- PostgreSQL conectado automaticamente pelo Blueprint;
- `/api/health` verificando aplicação e banco;
- inicialização idempotente do banco em `init_db.py`;
- callback Google OAuth compatível com HTTPS/proxy do Render;
- timezone `America/Sao_Paulo`;
- acesso restrito aos e-mails em `ALLOWED_GOOGLE_EMAILS`.

Leia **`RENDER-DEPLOY.md`** para o passo a passo.

## Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DEV_BYPASS_AUTH=1
python init_db.py
python app.py
```

Abra `http://localhost:5000/login`.

## Variáveis importantes

```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ALLOWED_GOOGLE_EMAILS=email1@gmail.com,email2@gmail.com
DATABASE_URL=postgresql://...
SECRET_KEY=...
COOKIE_SECURE=1
APP_TIMEZONE=America/Sao_Paulo
```

No Render via Blueprint, `DATABASE_URL` e `SECRET_KEY` são configuradas automaticamente. Você preenche apenas as credenciais Google e os e-mails autorizados.

## Funcionalidades

- leads compartilhados entre os dois usuários;
- reuniões vinculadas a leads e responsáveis;
- contratos vinculados a lead/usuário;
- contratos `Fechado` contabilizados automaticamente na meta mensal;
- metas de receita, contratos e reuniões da equipe e individuais;
- desempenho detalhado por usuário;
- histórico/auditoria das ações;
- importação em lote e exportação CSV/JSON;
- seed dos leads iniciais sem sobrescrever a base existente.
