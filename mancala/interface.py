"""Janela e navegação. Regras, reprodução e armazenamento ficam em módulos próprios."""
from datetime import datetime
from pathlib import Path
import logging
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
from .animacao import AnimadorJogada
from .estrategia import escolher_jogada
from .partidas import ArquivoPartidas, Partida
from .regras import CASAS, DEPOSITOS, casas_disponiveis
from .tutorial import ETAPAS

FUNDO = '#101f24'
PAINEL = '#1a3035'
TEXTO = '#f5eedc'
SUAVE = '#a3b9b5'
VERDE = '#bbdf96'
DOURADO = '#f0c277'


class Aplicativo:
    def __init__(self, janela, pasta_partidas=None):
        self.janela = janela
        janela.title('Mancala · uma casa, muitas possibilidades')
        janela.geometry('1120x760')
        janela.minsize(920, 680)
        janela.configure(bg=FUNDO)
        janela.protocol('WM_DELETE_WINDOW', self.sair)
        self.arquivos = ArquivoPartidas(pasta_partidas or Path(__file__).resolve().parents[1] / 'partidas_salvas')
        self.partida = None
        self.animador = AnimadorJogada()
        self.cancelamento = None
        self.respostas = queue.Queue()
        self.geracao = 0
        self.calculando = False
        self.tela = ''
        self.etapa = None
        self.etapa_concluida = False
        self.destaque = None
        self.na_mao = 0
        self.resumo_jogada = ''
        self.erro_salvamento = False
        topo = tk.Frame(janela, bg=FUNDO)
        topo.pack(fill='x', padx=28, pady=(20, 10))
        tk.Label(topo, text='M A N C A L A', font=('Segoe UI', 18, 'bold'), fg=VERDE, bg=FUNDO).pack(side='left')
        self.botao(topo, 'Sair', self.sair).pack(side='right', padx=(8, 0))
        self.botao(topo, 'Menu', self.menu).pack(side='right')
        self.conteudo = tk.Frame(janela, bg=FUNDO)
        self.conteudo.pack(fill='both', expand=True, padx=28, pady=12)
        self.status = tk.StringVar(value='48 sementes · 12 casas · depósitos P7 e P13')
        tk.Label(janela, textvariable=self.status, bg=FUNDO, fg=SUAVE,
                 font=('Segoe UI', 10), anchor='w').pack(fill='x', padx=28, pady=(0, 16))
        self.ultimo_quadro = time.monotonic()
        self.menu()
        self.temporizador = janela.after(40, self.atualizar)

    def botao(self, pai, texto, acao, principal=False):
        return tk.Button(pai, text=texto, command=acao, bg=VERDE if principal else PAINEL,
                         fg=FUNDO if principal else TEXTO, activebackground=DOURADO,
                         activeforeground=FUNDO, font=('Segoe UI', 12, 'bold'),
                         relief='flat', bd=0, padx=20, pady=12, cursor='hand2',
                         highlightthickness=1, highlightbackground=SUAVE)

    def texto(self, texto, tamanho=14, cor=TEXTO):
        rotulo = tk.Label(self.conteudo, text=texto, font=('Segoe UI', tamanho),
                          fg=cor, bg=FUNDO, anchor='w', justify='left', wraplength=850)
        rotulo.pack(anchor='w', pady=(0, 14))
        return rotulo

    def interromper_calculo(self):
        self.geracao += 1
        if self.cancelamento:
            self.cancelamento.set()
        self.calculando = False

    def limpar_tela(self, nome):
        self.interromper_calculo()
        self.animador = AnimadorJogada()
        self.tela = nome
        for filho in self.conteudo.winfo_children():
            filho.destroy()

    def menu(self):
        if self.partida and self.etapa is None:
            self.salvar()
        self.limpar_tela('menu')
        self.partida = None
        self.etapa = None
        self.texto('Uma casa. Muitas possibilidades.', 32, VERDE)
        self.texto('Escolha onde começar. O caminho das sementes revela a estratégia.', 15, SUAVE)
        for titulo, acao in [('Jogar', self.escolher_modo), ('Carregar jogo', self.listar_partidas),
                             ('Tutorial', lambda: self.iniciar_tutorial(0))]:
            self.botao(self.conteudo, titulo, acao, titulo == 'Jogar').pack(fill='x', pady=8, ipady=8)
        self.texto('P7 pertence a A · P13 pertence a B\nSementes depositadas ficam guardadas até o fim.', 13, SUAVE)

    def escolher_modo(self):
        self.limpar_tela('modo')
        self.texto('Como você quer jogar?', 30, VERDE)
        self.botao(self.conteudo, 'Jogador × jogador', lambda: self.iniciar(Partida()), True).pack(fill='x', pady=12)
        self.botao(self.conteudo, 'Jogador × máquina', self.escolher_dificuldade).pack(fill='x', pady=12)

    def escolher_dificuldade(self):
        self.limpar_tela('dificuldade')
        self.texto('Escolha seu desafio', 30, VERDE)
        descricoes = {'Fácil': 'Escolhas variadas entre casas disponíveis.',
                      'Normal': 'Antecipa respostas, capturas e turnos extras.',
                      'Difícil': 'Busca mais profunda, até 4 segundos por escolha. Sem vantagens artificiais.'}
        for nivel, descricao in descricoes.items():
            self.botao(self.conteudo, nivel, lambda n=nivel: self.iniciar(Partida('maquina', n)),
                       nivel == 'Difícil').pack(fill='x', pady=(12, 6))
            self.texto(descricao, 12, SUAVE)

    def listar_partidas(self):
        self.limpar_tela('carregar')
        self.texto('Suas partidas', 30, VERDE)
        self.texto('Mais recentes primeiro. Partidas concluídas também ficam disponíveis.', 13, SUAVE)
        registros, erros = self.arquivos.listar()
        quadro = tk.Frame(self.conteudo, bg=FUNDO)
        quadro.pack(fill='both', expand=True)
        lista = tk.Listbox(quadro, bg=PAINEL, fg=TEXTO, selectbackground=VERDE,
                           selectforeground=FUNDO, font=('Segoe UI', 12), bd=0,
                           activestyle='none', exportselection=False)
        barra = tk.Scrollbar(quadro, command=lista.yview)
        lista.configure(yscrollcommand=barra.set)
        barra.pack(side='right', fill='y')
        lista.pack(fill='both', expand=True)
        for instante, _, partida in registros:
            data = datetime.fromtimestamp(instante).strftime('%d/%m/%Y %H:%M')
            modo = 'Dupla' if partida.modo == 'dupla' else f'Máquina · {partida.dificuldade}'
            situacao = 'Concluída' if partida.estado.encerrada else 'Em andamento'
            a, b = partida.estado.placar
            lista.insert('end', f'{data}   |   {modo}   |   {situacao}   |   {a} × {b}   |   {partida.jogadas} jogadas')

        def abrir():
            if lista.curselection():
                self.iniciar(registros[lista.curselection()[0]][2])

        self.botao(self.conteudo, 'Abrir partida selecionada', abrir, True).pack(anchor='w', pady=16)
        lista.bind('<Double-Button-1>', lambda _: abrir())
        lista.bind('<Return>', lambda _: abrir())
        if registros:
            lista.selection_set(0)
        else:
            self.texto('Você ainda não tem partidas salvas.', 14, SUAVE)
        if erros:
            self.texto(f'{len(erros)} arquivo(s) inválido(s) foram ignorados; os arquivos originais foram preservados.', 12, DOURADO)

    def iniciar_tutorial(self, indice):
        self.etapa = indice
        self.etapa_concluida = False
        self.iniciar(Partida(estado=ETAPAS[indice].estado), tutorial=True)

    def iniciar(self, partida, tutorial=False):
        self.limpar_tela('partida')
        if not tutorial:
            self.etapa = None
        self.partida = partida
        self.tabuleiro_exibido = partida.estado.sementes
        self.na_mao = 0
        self.destaque = None
        self.titulo = self.texto('', 26, VERDE)
        self.mensagem = tk.StringVar()
        tk.Label(self.conteudo, textvariable=self.mensagem, fg=TEXTO, bg=FUNDO,
                 font=('Segoe UI', 13), wraplength=860, justify='left', anchor='w', height=3).pack(fill='x')
        self.tabuleiro = tk.Canvas(self.conteudo, bg=FUNDO, highlightthickness=0, height=350)
        self.tabuleiro.pack(fill='both', expand=True)
        self.tabuleiro.bind('<Configure>', lambda _: self.desenhar_tabuleiro())
        self.tabuleiro.bind('<Button-1>', self.clicar_tabuleiro)
        controles = tk.Frame(self.conteudo, bg=FUNDO)
        controles.pack(fill='x', pady=10)
        self.botoes_casas = []
        for coluna in range(6):
            botao = self.botao(controles, str(coluna+1), lambda c=coluna: self.escolher_coluna(c))
            botao.pack(side='left', expand=True, fill='x', padx=3)
            self.botoes_casas.append(botao)
        rodape = tk.Frame(self.conteudo, bg=FUNDO)
        rodape.pack(fill='x', pady=6)
        if tutorial:
            self.botao(rodape, 'Repetir etapa', lambda: self.iniciar_tutorial(self.etapa)).pack(side='left')
            self.avancar_tutorial = self.botao(rodape, 'Próxima etapa', self.proxima_etapa, True)
            self.avancar_tutorial.pack(side='right')
        else:
            self.botao(rodape, 'Salvar agora', self.salvar).pack(side='left')
            self.botao(rodape, 'Nova partida', self.escolher_modo).pack(side='right')
            self.salvar()
        self.mensagem.set(ETAPAS[self.etapa].instrucao if tutorial else 'Escolha uma casa sua com sementes. A joga embaixo; B joga em cima.')
        self.atualizar_controles()

    def proxima_etapa(self):
        if self.etapa_concluida:
            if self.etapa + 1 < len(ETAPAS):
                self.iniciar_tutorial(self.etapa + 1)
            else:
                self.menu()

    def nome_jogador(self, jogador):
        return 'Máquina' if jogador == 1 and self.partida.modo == 'maquina' else ('Jogador A', 'Jogador B')[jogador]

    def pode_jogar(self):
        return (not self.animador.ativo and not self.calculando and not self.partida.estado.encerrada
                and not (self.partida.modo == 'maquina' and self.partida.estado.jogador_atual == 1)
                and not (self.etapa is not None and self.etapa_concluida))

    def escolher_coluna(self, coluna):
        jogador = self.partida.estado.jogador_atual
        casas = CASAS[0] if jogador == 0 else tuple(reversed(CASAS[1]))
        self.selecionar_casa(casas[coluna])

    def clicar_tabuleiro(self, evento):
        for posicao, (x1, y1, x2, y2) in self.areas.items():
            if x1 <= evento.x <= x2 and y1 <= evento.y <= y2:
                self.selecionar_casa(posicao)
                break

    def selecionar_casa(self, casa):
        if not self.pode_jogar():
            return
        if self.etapa is not None and casa != ETAPAS[self.etapa].casa:
            self.mensagem.set(ETAPAS[self.etapa].instrucao)
            return
        try:
            self.executar_jogada(casa)
        except ValueError as erro:
            self.mensagem.set(str(erro))

    def executar_jogada(self, casa):
        resultado = self.partida.jogar(casa)
        self.animador.iniciar(resultado.eventos)
        self.resumo_jogada = (f'Captura de {resultado.capturadas} sementes. ' if resultado.capturadas else '')
        self.resumo_jogada += 'A última semente caiu no depósito: jogue novamente.' if resultado.turno_extra else 'Jogada concluída.'
        if self.etapa is None:
            self.salvar()
        self.atualizar_controles()

    def salvar(self):
        if not self.partida or self.etapa is not None:
            return
        try:
            self.arquivos.salvar(self.partida)
            self.status.set('Partida salva · ' + datetime.now().strftime('%H:%M:%S') + ' · 48 sementes conservadas')
            self.erro_salvamento = False
        except OSError as erro:
            self.erro_salvamento = True
            self.status.set(f'Não foi possível salvar: {erro}')

    def iniciar_calculo(self):
        self.calculando = True
        self.cancelamento = threading.Event()
        cancelar, estado, geracao = self.cancelamento, self.partida.estado, self.geracao
        dificuldade = self.partida.dificuldade
        self.mensagem.set(f'Máquina pensando · {dificuldade}. Menu e Sair continuam disponíveis.')
        self.atualizar_controles()

        def calcular():
            try:
                resposta = escolher_jogada(estado, dificuldade, cancelar)
                self.respostas.put((geracao, resposta, None))
            except Exception as erro:
                logging.exception('Falha na busca do computador')
                self.respostas.put((geracao, None, str(erro)))

        threading.Thread(target=calcular, daemon=True, name='estrategia-mancala').start()

    def atualizar(self):
        agora = time.monotonic()
        decorrido = min(agora - self.ultimo_quadro, 0.2)
        self.ultimo_quadro = agora
        if self.tela == 'partida':
            if self.animador.ativo:
                evento = self.animador.avancar(decorrido)
                if evento:
                    self.tabuleiro_exibido = evento.sementes
                    self.na_mao, self.destaque = evento.na_mao, evento.posicao
                    mensagens = {'retirada': 'Sementes retiradas da casa escolhida.',
                                 'distribuicao': f'Próxima posição: P{evento.posicao}.',
                                 'captura': 'Captura: sementes transferidas para o depósito.',
                                 'recolha': 'Lado vazio: recolhendo as sementes restantes.'}
                    self.mensagem.set(mensagens[evento.tipo] + f' Na mão: {evento.na_mao}.')
                    if not self.animador.ativo:
                        self.tabuleiro_exibido = self.partida.estado.sementes
                        self.mensagem.set(self.resumo_jogada)
                        if self.etapa is not None:
                            self.etapa_concluida = True
                            self.mensagem.set(ETAPAS[self.etapa].conclusao)
                    self.atualizar_controles()
            elif self.calculando:
                try:
                    geracao, resposta, erro = self.respostas.get_nowait()
                    if geracao == self.geracao:
                        self.calculando = False
                        if erro:
                            self.mensagem.set('Cálculo interrompido. Retome esta partida pelo menu para tentar novamente.')
                            self.partida.modo = 'dupla'
                            messagebox.showerror('Falha no computador', erro + '\nA partida passou para controle humano.')
                        else:
                            self.executar_jogada(resposta.casa)
                except queue.Empty:
                    pass
            elif (self.partida.modo == 'maquina' and self.partida.estado.jogador_atual == 1
                  and not self.partida.estado.encerrada):
                self.iniciar_calculo()
        self.temporizador = self.janela.after(40, self.atualizar)

    def atualizar_controles(self):
        estado = self.partida.estado
        if self.etapa is not None:
            titulo = ETAPAS[self.etapa].titulo
            self.avancar_tutorial.configure(state='normal' if self.etapa_concluida else 'disabled',
                                            text='Concluir tutorial' if self.etapa == len(ETAPAS)-1 else 'Próxima etapa')
        elif estado.encerrada and not self.animador.ativo:
            titulo = 'Empate' if estado.vencedor is None else self.nome_jogador(estado.vencedor) + ' venceu'
            self.mensagem.set(f'Placar final: A {estado.placar[0]} × {estado.placar[1]} B. Todas as sementes estão guardadas nos depósitos.')
        else:
            titulo = 'Distribuindo sementes' if self.animador.ativo else 'Vez de ' + self.nome_jogador(estado.jogador_atual)
        self.titulo.configure(text=titulo)
        casas = CASAS[0] if estado.jogador_atual == 0 else tuple(reversed(CASAS[1]))
        for botao, casa in zip(self.botoes_casas, casas):
            habilitado = self.pode_jogar() and casa in casas_disponiveis(estado)
            if self.etapa is not None:
                habilitado = habilitado and casa == ETAPAS[self.etapa].casa
            botao.configure(text=f'P{casa}', state='normal' if habilitado else 'disabled')
        self.desenhar_tabuleiro()

    def desenhar_tabuleiro(self):
        canvas = self.tabuleiro
        canvas.delete('all')
        largura, altura = max(canvas.winfo_width(), 860), max(canvas.winfo_height(), 280)
        escala = min(largura / 1000, altura / 340)
        dx, dy = (largura-1000*escala)/2, (altura-340*escala)/2
        self.areas = {}
        pontos = {13: (20, 90, 112, 270), 7: (888, 90, 980, 270)}
        for coluna in range(6):
            x = 135 + coluna * 123
            pontos[CASAS[0][coluna]] = (x, 202, x+108, 294)
            pontos[tuple(reversed(CASAS[1]))[coluna]] = (x, 62, x+108, 154)
        canvas.create_text(dx+500*escala, dy+20*escala, text='B   ←   ←   ←   ←   ←   ←',
                           fill=SUAVE, font=('Segoe UI', 13, 'bold'))
        canvas.create_text(dx+500*escala, dy+327*escala, text='A   →   →   →   →   →   →',
                           fill=VERDE, font=('Segoe UI', 13, 'bold'))
        for posicao, limites in pontos.items():
            x1, y1, x2, y2 = [limites[i]*escala + (dx if i%2 == 0 else dy) for i in range(4)]
            self.areas[posicao] = (x1, y1, x2, y2)
            disponivel = self.pode_jogar() and posicao in casas_disponiveis(self.partida.estado)
            cor = DOURADO if posicao == self.destaque else VERDE if disponivel else SUAVE
            canvas.create_oval(x1, y1, x2, y2, fill=PAINEL, outline=cor, width=3 if disponivel else 1)
            valor = self.tabuleiro_exibido[posicao]
            cx, cy = (x1+x2)/2, (y1+y2)/2
            for semente in range(valor):
                angulo = semente * 2.399963
                raio = math.sqrt((semente+1)/max(valor, 1))
                x = cx + math.cos(angulo)*raio*(x2-x1)*0.39
                y = cy + math.sin(angulo)*raio*(y2-y1)*0.36
                canvas.create_oval(x-2.5*escala, y-2.5*escala, x+2.5*escala, y+2.5*escala, fill=DOURADO, outline='')
            canvas.create_oval(cx-19*escala, cy-19*escala, cx+19*escala, cy+19*escala, fill=PAINEL, outline='')
            canvas.create_text(cx, cy, text=str(valor), fill=TEXTO, font=('Segoe UI', max(12, int(22*escala)), 'bold'))
            label = f'P{posicao}' + (' · depósito' if posicao in DEPOSITOS else '')
            canvas.create_text(cx, y1-12*escala, text=label, fill=cor, font=('Segoe UI', max(9, int(11*escala))))
        canvas.create_text(dx+500*escala, dy+180*escala, text=f'{sum(self.tabuleiro_exibido)} no tabuleiro  +  {self.na_mao} na mão  =  48',
                           fill=SUAVE, font=('Segoe UI', 11))

    def sair(self):
        self.salvar()
        if self.erro_salvamento and not messagebox.askyesno('Sair sem salvar?', 'O salvamento falhou. Deseja sair mesmo assim?'):
            return
        self.interromper_calculo()
        self.janela.after_cancel(self.temporizador)
        self.janela.destroy()
