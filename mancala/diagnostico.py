"""Verificação real de Tk, menus, jogadas e persistência no pacote distribuído."""
import json
from pathlib import Path
import tempfile
import traceback
import sys


def verificar_instalacao(caminho_relatorio):
    relatorio = {'sucesso': False, 'empacotado': bool(getattr(sys, 'frozen', False)),
                 'executavel': Path(sys.executable).name, 'verificacoes': []}
    janela = None
    try:
        import tkinter as tk
        from .interface import Aplicativo
        from .partidas import Partida
        from .tutorial import ETAPAS

        janela = tk.Tk()
        janela.withdraw()
        relatorio['tcl_tk'] = str(janela.tk.call('info', 'patchlevel'))
        with tempfile.TemporaryDirectory(prefix='mancala-verificacao-') as pasta:
            app = Aplicativo(janela, pasta)
            for acao in (app.escolher_modo, app.escolher_dificuldade, app.menu, app.listar_partidas):
                acao()
                janela.update_idletasks()
            relatorio['verificacoes'].append('menus')

            def concluir_animacao():
                for _ in range(80):
                    if not app.animador.ativo:
                        return
                    janela.after_cancel(app.temporizador)
                    app.animador.espera = 0
                    app.atualizar()
                    janela.update_idletasks()
                raise RuntimeError('A animação não terminou.')

            app.iniciar(Partida())
            app.selecionar_casa(2)
            concluir_animacao()
            if app.partida.estado.sementes[7] != 1:
                raise RuntimeError('Placar inesperado após jogada de teste.')
            registros, erros = app.arquivos.listar()
            if erros or len(registros) != 1 or registros[0][2].estado != app.partida.estado:
                raise RuntimeError('O salvamento não corresponde à partida.')
            app.iniciar(registros[0][2])
            relatorio['verificacoes'].extend(['jogada e animação', 'salvar e carregar'])

            for indice, etapa in enumerate(ETAPAS):
                app.iniciar_tutorial(indice)
                app.selecionar_casa(etapa.casa)
                concluir_animacao()
                if not app.etapa_concluida:
                    raise RuntimeError(f'Falha no tutorial: {indice + 1}')
            relatorio['verificacoes'].append('cinco etapas do tutorial')
            from .estrategia import escolher_jogada
            from .regras import estado_inicial, casas_disponiveis
            for nivel in ('Fácil', 'Normal', 'Difícil'):
                recomendacao = escolher_jogada(estado_inicial(), nivel, limite_segundos=0.1)
                if recomendacao.casa not in casas_disponiveis(estado_inicial()):
                    raise RuntimeError(f'Jogada inválida no nível {nivel}.')
            relatorio['verificacoes'].append('três níveis do computador')
            app.sair()
            janela = None
        relatorio['sucesso'] = True
    except Exception:
        relatorio['erro'] = traceback.format_exc()
        raise
    finally:
        if janela is not None:
            janela.destroy()
        Path(caminho_relatorio).write_text(json.dumps(relatorio, ensure_ascii=False, indent=2), encoding='utf-8')
