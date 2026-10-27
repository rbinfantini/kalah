"""Verificação real de Tk, menus, jogadas e persistência no pacote distribuído."""
import json
from pathlib import Path
import tempfile
import traceback
import sys


def medir_abertura(caminho_relatorio):
    """Registra o instante do primeiro menu desenhado; o cronômetro é externo.

    Usa uma janela mapeada fora da tela e partidas temporárias. O mesmo modo
    deve existir nos dois pacotes comparados, para medir até o mesmo marco.
    """
    import time
    import tkinter as tk
    from .interface import Aplicativo
    from .tabuleiro import Tabuleiro

    with tempfile.TemporaryDirectory(prefix='mancala-abertura-') as pasta:
        janela = tk.Tk()
        janela.withdraw()
        app = None
        erros = []
        janela.report_callback_exception = lambda tipo, valor, pilha: erros.append(str(valor))
        try:
            app = Aplicativo(janela, pasta)
            janela.geometry('1200x800+10000+10000')
            janela.deiconify()
            janela.update()
            janela.update_idletasks()
            pronto_em = time.perf_counter()

            def tabuleiros(pai):
                for filho in pai.winfo_children():
                    if isinstance(filho, Tabuleiro):
                        yield filho
                    yield from tabuleiros(filho)

            desenhos = list(tabuleiros(janela))
            if erros or not desenhos or any(len(t.areas) != 14 for t in desenhos):
                raise RuntimeError(f'O menu não terminou de desenhar: {erros}')
            relatorio = {'pronto_em': pronto_em, 'empacotado': bool(getattr(sys, 'frozen', False)),
                         'resolucao': '1200x800', 'marco': 'menu e tabuleiro desenhados'}
            Path(caminho_relatorio).write_text(json.dumps(relatorio), encoding='utf-8')
        finally:
            if app is not None:
                app.sair()
            else:
                janela.destroy()


def verificar_instalacao(caminho_relatorio):
    relatorio = {'sucesso': False, 'empacotado': bool(getattr(sys, 'frozen', False)),
                 'executavel': Path(sys.executable).name, 'verificacoes': []}
    janela = None
    try:
        import tkinter as tk
        from .interface import Aplicativo
        from .partidas import Partida
        from .tutorial import ETAPAS
        from PIL import ImageTk
        from .graficos import renderizar_tabuleiro, renderizar_anel, renderizar_semente

        janela = tk.Tk()
        janela.withdraw()
        erros_tk = []
        janela.report_callback_exception = lambda tipo, valor, pilha: erros_tk.append(
            ''.join(traceback.format_exception(tipo, valor, pilha)))
        relatorio['tcl_tk'] = str(janela.tk.call('info', 'patchlevel'))
        def conferir(desenho):
            imagem = ImageTk.PhotoImage(desenho, master=janela)
            if (imagem.width(), imagem.height()) != desenho.size:
                raise RuntimeError('Falha ao transferir um desenho do Pillow para o Tk.')

        for largura in range(360, 1601, 40):
            conferir(renderizar_tabuleiro(largura))
            for tipo in ('ativa', 'foco', 'destaque'):
                conferir(renderizar_anel(tipo, largura))
        for tamanho in range(6, 31, 2):
            for cor in range(4):
                conferir(renderizar_semente(cor, tamanho))
        relatorio['verificacoes'].append('180 variações geradas com Pillow e exibidas pelo Tk')
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
            if erros_tk:
                raise RuntimeError('Erro em um evento da interface:\n' + '\n'.join(erros_tk))
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
