"""Integração local com widgets reais; dados de teste nunca entram nas partidas pessoais."""
from pathlib import Path
from tempfile import TemporaryDirectory
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import re
from mancala.interface import Aplicativo
from mancala.partidas import Partida
from mancala.regras import resolver_jogada
from mancala.tabuleiro import dentro_da_casa
from mancala.tutorial import ETAPAS


class TestInterface(unittest.TestCase):
    def setUp(self):
        self.pasta = TemporaryDirectory()
        self.addCleanup(self.pasta.cleanup)
        try:
            self.janela = tk.Tk()
        except tk.TclError as erro:
            self.skipTest(f'Tk indisponível neste ambiente: {erro}')
        self.janela.withdraw()
        self.erros_tk = []
        self.janela.report_callback_exception = lambda tipo, valor, pilha: self.erros_tk.append(str(valor))
        self.app = Aplicativo(self.janela, self.pasta.name)
        self.addCleanup(self.fechar)

    def tearDown(self):
        if hasattr(self, 'erros_tk'):
            self.assertEqual(self.erros_tk, [])

    def fechar(self):
        if self.janela.winfo_exists():
            self.janela.update_idletasks()
            self.app.sair()


    def iniciar_turno_maquina(self, instante=100.0):
        partida = Partida(modo='maquina')
        partida.jogar(0)
        self.app.iniciar(partida)
        with patch('mancala.interface.threading.Thread'), patch('mancala.interface.time.monotonic', return_value=instante):
            self.app.iniciar_calculo()
        return self.app.geracao

    def test_maquina_espera_cinco_segundos_com_resposta_pronta(self):
        geracao = self.iniciar_turno_maquina()
        self.app.respostas.put((geracao, SimpleNamespace(casa=12), None))
        self.app.receber_jogada_maquina(104.99)
        self.assertTrue(self.app.calculando)
        self.assertEqual(self.app.partida.jogadas, 1)
        self.assertFalse(self.app.pode_jogar())
        self.app.receber_jogada_maquina(105.0)
        self.assertFalse(self.app.calculando)
        self.assertEqual(self.app.partida.jogadas, 2)

    def test_maquina_nao_soma_cinco_segundos_ao_tempo_de_busca(self):
        geracao = self.iniciar_turno_maquina()
        self.app.receber_jogada_maquina(105.1)
        self.assertTrue(self.app.calculando)
        self.app.respostas.put((geracao, SimpleNamespace(casa=12), None))
        self.app.receber_jogada_maquina(106.0)
        self.assertEqual(self.app.partida.jogadas, 2)

    def test_voltar_cancela_espera_e_descarta_resposta_antiga(self):
        geracao_antiga = self.iniciar_turno_maquina()
        self.app.voltar()
        self.assertEqual(self.app.tela, 'menu')
        self.assertFalse(self.app.calculando)
        geracao = self.iniciar_turno_maquina(instante=200.0)
        self.app.respostas.put((geracao_antiga, SimpleNamespace(casa=12), None))
        self.app.respostas.put((geracao, SimpleNamespace(casa=12), None))
        self.app.receber_jogada_maquina(205.0)
        self.assertEqual(self.app.partida.jogadas, 1)
        self.app.receber_jogada_maquina(205.04)
        self.assertEqual(self.app.partida.jogadas, 2)

    def test_ritmo_normal_aguarda_mais_que_o_rapido(self):
        def avancar_160_ms(ritmo):
            self.app.iniciar(Partida())
            self.app.velocidade.set(ritmo)
            self.app.selecionar_casa(0)
            self.app.animador.avancar(0)
            self.janela.after_cancel(self.app.temporizador)
            self.app.ultimo_quadro = 100.0
            with patch('mancala.interface.time.monotonic', return_value=100.16):
                self.app.atualizar()
            return self.app.animador.indice
        self.assertEqual(avancar_160_ms('Normal'), 1)
        self.assertEqual(avancar_160_ms('Rápido'), 2)

    def concluir_jogada(self):
        self.app.velocidade.set('Sem animação')
        self.janela.after_cancel(self.app.temporizador)
        self.app.atualizar()
        self.janela.update_idletasks()

    def test_tutorial_destaca_somente_a_casa_do_exercicio(self):
        self.app.iniciar_tutorial(2)
        self.assertEqual(self.app.casas_jogaveis(), (ETAPAS[2].casa,))
        self.app.selecionar_casa(0)
        self.assertEqual(self.app.partida.jogadas, 0)
        self.app.selecionar_casa(ETAPAS[2].casa)
        self.concluir_jogada()
        self.assertTrue(self.app.etapa_concluida)
        self.assertEqual(self.app.casas_jogaveis(), ())
        self.assertEqual(list(Path(self.pasta.name).glob('*.json')), [])

    def test_atalhos_respeitam_fileira_e_bloqueio_durante_animacao(self):
        self.app.iniciar(Partida())
        self.app.escolher_coluna(0)
        self.app.escolher_coluna(1)
        self.assertEqual(self.app.partida.jogadas, 1)
        self.concluir_jogada()
        esperado = resolver_jogada(self.app.partida.estado, 12).estado
        self.app.escolher_coluna(0)  # Na fileira B, a primeira casa à esquerda é P12.
        self.assertEqual(self.app.partida.estado, esperado)

    def test_voltar_preserva_resultado_mesmo_durante_animacao(self):
        self.app.iniciar(Partida())
        self.app.selecionar_casa(2)
        esperado = self.app.partida.estado
        self.app.voltar()
        self.assertEqual(self.app.tela, 'menu')
        registros, erros = self.app.arquivos.listar()
        self.assertFalse(erros)
        self.assertEqual(registros[0][2].estado, esperado)
        self.assertFalse(self.app.animador.ativo)
        self.app.atalho_casa(SimpleNamespace(widget=self.janela), 0)
        self.assertEqual(self.app.tela, 'menu')

    def test_sem_animacao_preserva_estado_e_contagem(self):
        self.app.iniciar(Partida())
        esperado = resolver_jogada(self.app.partida.estado, 2).estado
        self.app.selecionar_casa(2)
        self.concluir_jogada()
        self.assertEqual(self.app.tabuleiro_exibido, esperado.sementes)
        self.assertEqual(self.app.na_mao, 0)
        self.assertIsNone(self.app.destaque)
        self.assertTrue(self.app.pode_jogar())

    def test_foco_percorre_casas_validas_e_confirma(self):
        self.app.iniciar(Partida())
        tabuleiro = self.app.tabuleiro
        tabuleiro.foco = 0
        tabuleiro.mover_foco(1)
        self.assertEqual(tabuleiro.foco, 1)
        tabuleiro.confirmar(None)
        self.assertEqual(self.app.partida.jogadas, 1)
        tabuleiro.confirmar(None)
        self.assertEqual(self.app.partida.jogadas, 1)

    def test_area_clicavel_exclui_cantos_da_elipse(self):
        self.assertTrue(dentro_da_casa(50, 40, (0, 0, 100, 80)))
        self.assertFalse(dentro_da_casa(1, 1, (0, 0, 100, 80)))

    def test_graficos_reutilizados_e_liberados_ao_sair_da_tela(self):
        self.app.iniciar(Partida())
        self.janela.geometry('1100x680+1800+100')
        self.janela.deiconify()
        self.janela.update()
        tabuleiro = self.app.tabuleiro
        sementes = [0] * 14
        sementes[0] = 48
        tabuleiro.atualizar(sementes, (0,))
        imagens = dict(tabuleiro.imagens)
        tabuleiro.atualizar(sementes, (0,))
        self.assertEqual(tabuleiro.imagens, imagens)
        self.assertEqual(sum(tabuleiro.type(item) == 'image'
                             for item in tabuleiro.find_all()), 50)  # Madeira, anel e 48 sementes.
        nomes = {str(imagem) for imagem in imagens.values()}
        imagens.clear()
        self.app.menu()
        self.assertFalse(nomes.intersection(self.janela.tk.call('image', 'names')))

    def test_tabuleiro_mantem_casas_circulares_ao_redimensionar(self):
        self.app.iniciar(Partida())
        self.janela.deiconify()
        for tamanho in ('900x640', '1100x680', '1200x800'):
            self.janela.geometry(tamanho + '+1800+100')
            self.janela.update()
            self.assertEqual(len(self.app.tabuleiro.areas), 14)
            for casa, (x1, y1, x2, y2) in self.app.tabuleiro.areas.items():
                if casa not in (7, 13):
                    self.assertAlmostEqual(x2-x1, y2-y1)
            textos = [self.app.tabuleiro.itemcget(item, 'text')
                      for item in self.app.tabuleiro.find_all()
                      if self.app.tabuleiro.type(item) == 'text']
            self.assertFalse(any(re.search(r'\bP\d+\b', texto) for texto in textos))

    def test_tutorial_e_mensagens_nao_exibem_codigos_de_posicao(self):
        for indice, etapa in enumerate(ETAPAS):
            self.assertNotRegex(etapa.instrucao + etapa.conclusao, r'\bP\d+\b')
            self.app.iniciar_tutorial(indice)
            self.app.selecionar_casa(etapa.casa)
            self.concluir_jogada()
            self.assertNotRegex(self.app.mensagem.get(), r'\bP\d+\b')
        self.app.iniciar(Partida())
        self.app.selecionar_casa(2)
        self.concluir_jogada()
        self.assertNotRegex(self.app.mensagem.get(), r'\bP\d+\b')

    def widgets(self, pai):
        for filho in pai.winfo_children():
            yield filho
            yield from self.widgets(filho)

    def test_filtro_de_partidas_preserva_selecao_correta(self):
        aberta = Partida()
        encerrada = Partida(estado=ETAPAS[-1].estado)
        encerrada.jogar(ETAPAS[-1].casa)
        for partida in (aberta, encerrada):
            self.app.arquivos.salvar(partida)
        self.app.listar_partidas()
        lista = next(w for w in self.widgets(self.app.conteudo) if isinstance(w, ttk.Treeview))
        filtro = next(w for w in self.widgets(self.app.conteudo) if isinstance(w, ttk.Combobox))
        self.assertEqual(len(lista.get_children()), 2)
        filtro.set('Em andamento')
        filtro.event_generate('<<ComboboxSelected>>')
        self.assertEqual(len(lista.get_children()), 1)
        abrir = next(w for w in self.widgets(self.app.conteudo)
                     if isinstance(w, ttk.Button) and w.cget('text') == 'Abrir partida  →')
        abrir.invoke()
        self.assertEqual(self.app.partida.identificador, aberta.identificador)

    def test_controles_cabem_na_janela_minima(self):
        self.janela.geometry('900x640+1800+100')
        self.janela.deiconify()
        self.janela.update()
        telas = (self.app.menu, self.app.escolher_modo, self.app.escolher_dificuldade,
                 lambda: self.app.iniciar(Partida()), lambda: self.app.iniciar_tutorial(3),
                 self.app.listar_partidas)
        for abrir in telas:
            abrir()
            self.janela.update_idletasks()
            for widget in self.widgets(self.app.conteudo):
                if isinstance(widget, (tk.Label, ttk.Button, ttk.Combobox)):
                    with self.subTest(tela=self.app.tela, widget=str(widget)):
                        self.assertGreater(widget.winfo_height(), 1)
                        self.assertLessEqual(widget.winfo_y()+widget.winfo_height(),
                                             widget.master.winfo_height()+2)


if __name__ == '__main__':
    unittest.main()
