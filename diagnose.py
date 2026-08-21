"""Diagnóstico simples para executar no Render Shell ou localmente."""
from sqlalchemy import text
from app import app, db, DATABASE_URI


def mask_uri(uri: str) -> str:
    if "@" not in uri:
        return uri
    prefix, rest = uri.split("@", 1)
    if "://" in prefix:
        scheme, _ = prefix.split("://", 1)
        return f"{scheme}://***:***@{rest}"
    return f"***@{rest}"


with app.app_context():
    print("DATABASE:", mask_uri(DATABASE_URI))
    row = db.session.execute(text("SELECT current_database(), current_user")).first()
    print("POSTGRES OK:", row)
    tables = db.session.execute(text("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")).all() if DATABASE_URI.startswith("postgresql://") else []
    if tables:
        print("TABELAS:", ", ".join(x[0] for x in tables))
