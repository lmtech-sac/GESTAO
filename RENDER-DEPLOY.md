# LM TECH CRM — Render

## Configuração do Web Service

**Build Command**
```bash
pip install --upgrade pip && pip install -r requirements.txt && python verify_dependencies.py
```

**Start Command**
```bash
gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --keep-alive 5 --access-logfile - --error-logfile - --capture-output
```

O próprio `app.py` espera o PostgreSQL responder e executa `db.create_all()` + seed inicial.
Não é obrigatório executar `init_db.py` no Start Command.

## Environment Variables

- `PYTHON_VERSION=3.12.11`
- `DATABASE_URL=<Internal Database URL do Render Postgres>`
- `SECRET_KEY=<chave aleatória grande>`
- `APP_TIMEZONE=America/Sao_Paulo`
- `COOKIE_SECURE=1`
- `DEV_BYPASS_AUTH=0`
- `AUTO_INIT_DB=1`
- `DB_STARTUP_ATTEMPTS=40`
- `DB_STARTUP_DELAY=2`
- `GOOGLE_CLIENT_ID=<depois>`
- `GOOGLE_CLIENT_SECRET=<depois>`
- `ALLOWED_GOOGLE_EMAILS=email1@gmail.com,email2@gmail.com`

## Se aparecer `No module named requests`
Esta versão declara `requests>=2.32,<3` explicitamente. Depois de enviar os arquivos novos, use **Clear build cache & deploy** para forçar a instalação do `requirements.txt` atualizado.

## Verificação
Durante o build deve aparecer:
```text
[LM TECH] Python: 3.12.11
[LM TECH] Dependências principais OK.
```

Durante o start deve aparecer:
```text
[LM TECH] Banco pronto e tabelas verificadas (...)
```

Depois:
- `/healthz` => serviço vivo
- `/api/health` => banco PostgreSQL acessível

## Google OAuth
Redirect URI:
```text
https://SEU-SERVICO.onrender.com/auth/google/callback
```
