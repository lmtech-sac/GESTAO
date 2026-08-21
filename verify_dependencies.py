"""Falha o BUILD do Render cedo se uma dependência essencial estiver ausente."""
import sys

MODULES = [
    "flask",
    "flask_sqlalchemy",
    "sqlalchemy",
    "authlib",
    "requests",
    "gunicorn",
    "psycopg2",
]

failed = []
for name in MODULES:
    try:
        __import__(name)
    except Exception as exc:
        failed.append(f"{name}: {exc}")

print(f"[LM TECH] Python: {sys.version.split()[0]}")
if failed:
    print("[LM TECH] Dependências ausentes/quebradas:")
    for item in failed:
        print(" -", item)
    raise SystemExit(1)

print("[LM TECH] Dependências principais OK.")
