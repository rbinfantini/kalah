"""Mantém os dados graváveis fora das bibliotecas do executável empacotado."""
import os
from pathlib import Path
import sys


def pasta_dados():
    if getattr(sys, 'frozen', False):
        base = os.environ.get('LOCALAPPDATA')
        return (Path(base) if base else Path.home() / 'AppData' / 'Local') / 'MancalaSoJoga'
    # Preserva os saves existentes de quem executa o código-fonte.
    return Path(__file__).resolve().parents[1]
