"""Entrada compartilhada pelo código, pelo atalho Python e pelo executável."""
import argparse
import logging
import sys
from .caminhos import pasta_dados


def main():
    argumentos = argparse.ArgumentParser(description='Mancala Só Joga')
    argumentos.add_argument('--verificar-instalacao', metavar='RELATORIO',
                            help='verifica o pacote e grava um relatório JSON')
    opcoes = argumentos.parse_args()
    if opcoes.verificar_instalacao:
        from .diagnostico import verificar_instalacao
        verificar_instalacao(opcoes.verificar_instalacao)
        return
    import tkinter as tk
    from .interface import Aplicativo
    janela = tk.Tk()
    Aplicativo(janela)
    janela.mainloop()


def iniciar():
    try:
        main()
    except Exception:
        # Falhas precisam ser diagnosticáveis mesmo sem um console.
        destino = pasta_dados() / 'logs' / 'inicializacao.log'
        detalhe = 'Não foi possível criar o arquivo de diagnóstico.'
        try:
            destino.parent.mkdir(parents=True, exist_ok=True)
            logging.basicConfig(filename=destino, encoding='utf-8', level=logging.ERROR,
                                format='%(asctime)s %(levelname)s %(message)s', force=True)
            logging.exception('Não foi possível iniciar Mancala Só Joga')
            detalhe = f'Detalhes em:\n{destino}'
        except OSError:
            pass
        mensagem = 'Não foi possível abrir o Mancala Só Joga.\n\n' + detalhe
        if '--verificar-instalacao' not in sys.argv:
            if sys.platform == 'win32':
                import ctypes
                ctypes.windll.user32.MessageBoxW(None, mensagem, 'Mancala Só Joga', 0x10)
            else:
                print(mensagem, file=sys.stderr)
        raise SystemExit(1)
