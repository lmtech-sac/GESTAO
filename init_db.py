import os
import sys
import time
from urllib.parse import urlsplit

from sqlalchemy import text

from app import app, db, initialize_database


def safe_db_label():
    raw = os.getenv("DATABASE_URL", "").strip()
    if not raw:
        return "sem DATABASE_URL"
    try:
        parsed = urlsplit(raw.replace("postgres://", "postgresql://", 1))
        return f"{parsed.scheme}://{parsed.hostname or '?'}:{parsed.port or 5432}/{(parsed.path or '/').lstrip('/')}"
    except Exception:
        return "DATABASE_URL configurada"


def main():
    max_attempts = int(os.getenv("DB_STARTUP_ATTEMPTS", "40"))
    delay = float(os.getenv("DB_STARTUP_DELAY", "2"))
    print(f"[LM TECH] Banco: {safe_db_label()}", flush=True)

    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            with app.app_context():
                db.session.execute(text("SELECT 1"))
                db.session.rollback()
            print(f"[LM TECH] PostgreSQL disponível (tentativa {attempt}/{max_attempts}).", flush=True)
            initialize_database()
            print("[LM TECH] Tabelas verificadas e seed concluído.", flush=True)
            return 0
        except Exception as exc:
            last_error = exc
            try:
                with app.app_context():
                    db.session.rollback()
            except Exception:
                pass
            print(
                f"[LM TECH] Banco ainda indisponível ({attempt}/{max_attempts}): "
                f"{exc.__class__.__name__}: {exc}",
                flush=True,
            )
            if attempt < max_attempts:
                time.sleep(delay)

    print("[LM TECH] ERRO FATAL: não foi possível conectar/inicializar o banco.", file=sys.stderr, flush=True)
    if last_error:
        print(f"[LM TECH] Último erro: {last_error!r}", file=sys.stderr, flush=True)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
