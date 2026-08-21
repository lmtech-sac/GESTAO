# LM TECH CRM — Advocacia

Backend real para o HTML do CRM da LM TECH.

## O que já está pronto

- Flask + SQLAlchemy.
- SQLite local e suporte a PostgreSQL por `DATABASE_URL`.
- Login com Google OAuth.
- Acesso restrito aos e-mails de `ALLOWED_GOOGLE_EMAILS` (ideal para os 2 usuários).
- Leads compartilhados no servidor.
- Reuniões vinculadas a um lead e a um usuário.
- Contratos vinculados a lead/usuário.
- Contrato com status `Fechado` soma automaticamente na receita realizada do mês.
- Metas mensais da equipe e metas individuais: receita, contratos e reuniões.
- Controle por usuário: receita, contratos, reuniões, reuniões realizadas, ações em leads e histórico recente.
- Log de auditoria das alterações.
- Scripts comerciais compartilhados.
- Importação em lote e exportação CSV/JSON no frontend.

## Rodar local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# exporte as variáveis do .env ou use seu gerenciador preferido
export DEV_BYPASS_AUTH=1
python app.py
```

Abra `http://localhost:5000/login` e use o botão de acesso de desenvolvimento. O bypass só aparece se `DEV_BYPASS_AUTH=1`.

## Google OAuth

No Google Cloud Console crie um OAuth Client do tipo Web e coloque como URI de redirecionamento:

- Local: `http://localhost:5000/auth/google/callback`
- Produção: `https://SEU-DOMINIO/auth/google/callback`

Depois defina:

```text
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
ALLOWED_GOOGLE_EMAILS=email1@gmail.com,email2@gmail.com
```

Se o e-mail autenticado não estiver nessa lista, o CRM não permite entrada.

## Banco em produção

Para produção, prefira PostgreSQL e coloque a URL em `DATABASE_URL`. Se deixar vazio, o app usa `lmtech.db` local.

## Deploy

O `render.yaml` já contém build e start command. Cadastre as variáveis secretas no painel do serviço e conecte um banco PostgreSQL pela variável `DATABASE_URL`.
