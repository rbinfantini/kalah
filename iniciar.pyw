"""Abra este arquivo no Windows para iniciar sem janela de terminal."""
from pathlib import Path
import logging
import sys


def iniciar():
    try:
        from main import main
        main()
    except Exception:
        # Mesmo sem console, uma falha precisa ficar visível e ser diagnosticável.
        destino = Path(__file__).resolve().parent / 'logs' / 'inicializacao.log'
        detalhe = 'Não foi possível criar o arquivo de diagnóstico.'
        try:
            destino.parent.mkdir(exist_ok=True)
            logging.basicConfig(filename=destino, encoding='utf-8', level=logging.ERROR,
                                format='%(asctime)s %(levelname)s %(message)s', force=True)
            logging.exception('Não foi possível iniciar Mancala')
            detalhe = f'Detalhes em:\n{destino}'
        except OSError:
            pass
        mensagem = 'Não foi possível abrir o Mancala.\nUse Python 3.10 ou superior com Tkinter.\n\n' + detalhe
        if sys.platform == 'win32':
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, mensagem, 'Mancala — falha na inicialização', 0x10)
        else:
            print(mensagem, file=sys.stderr)
        raise SystemExit(1)


if __name__ == '__main__':
    iniciar()
