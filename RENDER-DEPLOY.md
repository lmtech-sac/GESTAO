# LM TECH CRM — Deploy no Render

Este pacote foi ajustado para Render + PostgreSQL.

## Opção A — Blueprint (recomendada)

1. Extraia o ZIP.
2. Envie **os arquivos da raiz do ZIP** para a raiz do repositório GitHub.
3. No Render: **New > Blueprint**.
4. Conecte o repositório.
5. O Render lê `render.yaml` e cria/usa:
   - Web Service `lm-tech-crm`
   - PostgreSQL `lm-tech-crm-db`
6. Preencha as variáveis solicitadas:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `ALLOWED_GOOGLE_EMAILS` (ex.: `email1@gmail.com,email2@gmail.com`)
7. Acompanhe o log. A sequência saudável é:
   - `[LM TECH] Inicializando/verificando PostgreSQL...`
   - `[LM TECH] PostgreSQL disponível...`
   - `[LM TECH] Tabelas verificadas e seed concluído.`
   - `[LM TECH] Banco pronto. Iniciando Gunicorn...`

O startup tenta conectar ao banco por até ~80 segundos antes de encerrar com um erro claro.

## Se o Render disser que você já tem 1 Postgres Free

O Render permite apenas um banco PostgreSQL Free ativo por workspace. Se o banco do deploy anterior (`lm-tech-crm-db`) já existir, **não crie outro**.

Você pode:

- manter o `render.yaml` normal se o Blueprint reconhecer `lm-tech-crm-db`; ou
- usar `render-web-only.yaml` como `render.yaml` e preencher manualmente `DATABASE_URL` com a **Internal Database URL** do Postgres existente.

## Google Login

Quando o serviço estiver online, adicione no Google Cloud:

`https://SEU-SERVICO.onrender.com/auth/google/callback`

O app usa `RENDER_EXTERNAL_URL`, então gera o callback HTTPS automaticamente.

## Teste de saúde

- `/healthz` — liveness do Web Service (200 quando o Flask/Gunicorn está vivo)
- `/api/health` — testa também a conexão com o PostgreSQL

## Banco

Em Render, o CRM exige `DATABASE_URL`. Ele não faz fallback silencioso para SQLite em produção.

As tabelas são criadas automaticamente no startup. O seed dos leads só roda se a tabela `leads` estiver vazia.

## Comandos usados pelo Render

Build:

`python -m pip install --upgrade pip && python -m pip install -r requirements.txt`

Start:

`bash ./start.sh`

## Se ainda aparecer "exited with status 1"

Copie o bloco do log a partir de `[LM TECH]`. O novo startup mostra o erro real do banco/driver em vez de encerrar sem contexto.
