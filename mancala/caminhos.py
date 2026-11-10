"""Mantém os dados graváveis fora das bibliotecas do executável empacotado."""
import os
from pathlib import Path
import sys


def pasta_dados():
    """
    Retorna a pasta de dados persistentes do jogo conforme o modo de execução.

    Returns
    -------
    Path
        Diretório usado para partidas salvas e logs.

    Notes
    -----
    Apenas retorna o caminho, sem criar diretórios. No EXE, os dados
    ficam na área local do usuário, fora da extração temporária das
    bibliotecas do PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        base = os.environ.get('LOCALAPPDATA')
        return (Path(base) if base else Path.home() / 'AppData' / 'Local') / 'MancalaSoJoga'
    # Preserva os saves existentes de quem executa o código-fonte.
    return Path(__file__).resolve().parents[1]
