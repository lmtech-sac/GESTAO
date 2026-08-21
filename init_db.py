"""Inicialização manual opcional do banco.

O app também inicializa automaticamente no boot. Este arquivo continua útil
para diagnóstico ou execução manual no Render Shell.
"""
from app import initialize_database_with_retry


if __name__ == "__main__":
    initialize_database_with_retry()
    print("[LM TECH] Inicialização manual concluída.", flush=True)
