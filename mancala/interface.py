"""Janela e navegação. Regras, reprodução e armazenamento ficam em módulos próprios."""
from datetime import datetime
from pathlib import Path
import logging
import math
import queue
import threading
import time
import tkinter as tk
from tkinter import font as tkfont, messagebox
from .animacao import AnimadorJogada
from .estrategia import escolher_jogada
from .partidas import ArquivoPartidas, Partida
from .regras import CASAS, DEPOSITOS, casas_disponiveis
from .tutorial import ETAPAS

# Tabuleiro de madeira sobre tecido índigo.
FUNDO = '#1d2340'
PAINEL = '#283057'
PAINEL_ATIVO = '#343e6e'
TEXTO = '#ece2cc'
SUAVE = '#9aa3c2'
ACAFRAO = '#e8a93a'
CEU = '#9fc0e8'
MADEIRA = '#9a6136'
MADEIRA_ESCURA = '#6b3f20'
COVA = '#4a2a15'
COVA_CLARA = '#5c3720'
SOMBRA = '#2e1a0c'
CORES_SEMENTES = ('#e9dcc0', '#c9452f', '#3a322c', '#d8b36a', '#7d8b5a')
CORES_JOGADORES = (ACAFRAO, CEU)


def familia_fonte(janela):
    disponiveis = set(tkfont.families(janela))
    return next((f for f in ('Optima', 'Candara', 'Segoe UI') if f in disponiveis), 'Helvetica')


class Botao(tk.Frame):
    """tk.Button ignora cores no macOS; este botão mantém a aparência e aceita teclado."""

    def __init__(self, pai, titulo, acao, detalhe='', principal=False, fonte='Helvetica', tamanho=15):
        super().__init__(pai, takefocus=1, highlightthickness=2, highlightbackground=FUNDO,
                         highlightcolor=TEXTO, padx=22, pady=12 if detalhe else 10)
        self.acao, self.principal, self.ativo = acao, principal, True
        self.rotulo = tk.Label(self, text=titulo, font=(fonte, tamanho, 'bold'), anchor='w')
        self.rotulo.pack(fill='x')
        self.detalhe = tk.Label(self, text=detalhe, font=(fonte, 12), anchor='w') if detalhe else None
        if self.detalhe:
            self.detalhe.pack(fill='x')
        for parte in (self, self.rotulo, self.detalhe):
            if parte:
                parte.bind('<Button-1>', self.acionar)
                parte.bind('<Enter>', lambda _: self.pintar(True))
                parte.bind('<Leave>', lambda _: self.pintar(False))
        self.bind('<Return>', self.acionar)
        self.bind('<space>', self.acionar)
        self.pintar(False)

    def acionar(self, _=None):
        if self.ativo:
            self.focus_set()
            self.acao()

    def configurar(self, ativo=None, titulo=None):
        if ativo is not None:
            self.ativo = ativo
        if titulo is not None:
            self.rotulo.configure(text=titulo)
        self.pintar(False)

    def pintar(self, sobre):
        if not self.ativo:
            fundo, frente, detalhe = FUNDO, SUAVE, SUAVE
        elif self.principal:
            fundo, frente, detalhe = ('#f2bb57' if sobre else ACAFRAO), FUNDO, FUNDO
        else:
            fundo, frente, detalhe = (PAINEL_ATIVO if sobre else PAINEL), TEXTO, SUAVE
        cursor = 'hand2' if self.ativo else ''
        self.configure(bg=fundo, cursor=cursor)
        self.rotulo.configure(bg=fundo, fg=frente, cursor=cursor)
        if self.detalhe:
            self.detalhe.configure(bg=fundo, fg=detalhe, cursor=cursor)


class Aplicativo:
    def __init__(self, janela, pasta_partidas=None):
        self.janela = janela
        self.fonte = familia_fonte(janela)
        janela.title('Mancala')
        janela.geometry('1120x780')
        janela.minsize(920, 700)
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
        self.sob_mouse = None
        self.na_mao = 0
        self.resumo_jogada = ''
        self.erro_salvamento = False
        self.areas = {}
        topo = tk.Frame(janela, bg=FUNDO)
        topo.pack(fill='x', padx=40, pady=(24, 0))
        tk.Label(topo, text='Mancala', font=(self.fonte, 17, 'bold'), fg=TEXTO, bg=FUNDO).pack(side='left')
        self.botao(topo, 'Sair', self.sair, tamanho=13).pack(side='right', padx=(8, 0))
        self.botao(topo, 'Menu', self.menu, tamanho=13).pack(side='right')
        self.conteudo = tk.Frame(janela, bg=FUNDO)
        self.conteudo.pack(fill='both', expand=True, padx=40, pady=(20, 8))
        self.status = tk.StringVar(value='')
        tk.Label(janela, textvariable=self.status, bg=FUNDO, fg=SUAVE,
                 font=(self.fonte, 11), anchor='w').pack(fill='x', padx=40, pady=(0, 18))
        for coluna in range(6):
            janela.bind(str(coluna+1), lambda _, c=coluna: self.tela == 'partida' and self.escolher_coluna(c))
        self.ultimo_quadro = time.monotonic()
        self.menu()
        self.temporizador = janela.after(40, self.atualizar)

    def botao(self, pai, titulo, acao, detalhe='', principal=False, tamanho=15):
        return Botao(pai, titulo, acao, detalhe, principal, self.fonte, tamanho)

    def texto(self, texto, tamanho=14, cor=TEXTO, peso='normal', pai=None, espaco=14):
        rotulo = tk.Label(pai or self.conteudo, text=texto, font=(self.fonte, tamanho, peso),
                          fg=cor, bg=FUNDO, anchor='w', justify='left', wraplength=680)
        rotulo.pack(anchor='w', fill='x', pady=(0, espaco))
        return rotulo

    def coluna(self):
        """Telas de texto ficam numa coluna estreita, alinhada à esquerda."""
        quadro = tk.Frame(self.conteudo, bg=FUNDO)
        quadro.pack(anchor='nw', pady=(28, 0))
        return quadro

    def interromper_calculo(self):
        self.geracao += 1
        if self.cancelamento:
            self.cancelamento.set()
        self.calculando = False

    def limpar_tela(self, nome):
        self.interromper_calculo()
        self.animador = AnimadorJogada()
        self.tela = nome
        self.areas = {}
        for filho in self.conteudo.winfo_children():
            filho.destroy()

    def menu(self):
        if self.partida and self.etapa is None:
            self.salvar()
        self.limpar_tela('menu')
        self.partida = None
        self.etapa = None
        coluna = self.coluna()
        self.texto('Semeie, capture e guarde\nmais sementes que o adversário.', 34, TEXTO, 'bold', coluna, 30)
        opcoes = [('Novo jogo', 'Contra a máquina ou com alguém ao seu lado', self.novo_jogo),
                  ('Continuar partida', 'Retome uma partida salva', self.listar_partidas),
                  ('Aprender a jogar', f'{len(ETAPAS)} jogadas guiadas, uma regra por vez',
                   lambda: self.iniciar_tutorial(0))]
        botoes = [self.botao(coluna, titulo, acao, detalhe, titulo == 'Novo jogo') for titulo, detalhe, acao in opcoes]
        for botao in botoes:
            botao.pack(fill='x', pady=5)
        self.texto('Cada jogador tem seis casas e um depósito à sua direita.\n'
                   'Sementes que entram no depósito não saem mais.', 13, SUAVE, pai=coluna, espaco=0).pack(pady=(26, 0))
        self.status.set('')
        botoes[0].focus_set()

    def novo_jogo(self):
        self.limpar_tela('novo')
        coluna = self.coluna()
        self.texto('Novo jogo', 34, TEXTO, 'bold', coluna, 24)
        self.texto('Contra a máquina', 14, SUAVE, pai=coluna, espaco=6)
        descricoes = {'Fácil': 'Joga sem muito planejamento. Bom para aprender.',
                      'Normal': 'Prevê suas respostas, capturas e turnos extras.',
                      'Difícil': 'Pensa até 4 segundos por jogada, sem trapaças.'}
        for nivel, descricao in descricoes.items():
            self.botao(coluna, nivel, lambda n=nivel: self.iniciar(Partida('maquina', n)),
                       descricao, nivel == 'Normal').pack(fill='x', pady=4)
        self.texto('Dois jogadores', 14, SUAVE, pai=coluna, espaco=6).pack(pady=(22, 0))
        self.botao(coluna, 'Jogar neste computador', lambda: self.iniciar(Partida()),
                   'Vocês se revezam no mesmo teclado e mouse.').pack(fill='x', pady=4)

    def listar_partidas(self):
        self.limpar_tela('carregar')
        coluna = self.coluna()
        coluna.pack_configure(fill='both', expand=True)
        self.texto('Partidas salvas', 34, TEXTO, 'bold', coluna, 8)
        registros, erros = self.arquivos.listar()
        if not registros:
            self.texto('Nenhuma partida salva ainda. Partidas são salvas sozinhas a cada jogada.', 14, SUAVE, pai=coluna, espaco=20)
            self.botao(coluna, 'Começar um novo jogo', self.novo_jogo, principal=True).pack(anchor='w')
        else:
            self.texto('Mais recentes primeiro. Clique duas vezes ou pressione Enter para abrir.', 13, SUAVE, pai=coluna, espaco=16)
            quadro = tk.Frame(coluna, bg=PAINEL)
            quadro.pack(fill='both', expand=True, anchor='w')
            lista = tk.Listbox(quadro, bg=PAINEL, fg=TEXTO, selectbackground=ACAFRAO, selectforeground=FUNDO,
                               font=(self.fonte, 14), bd=0, highlightthickness=0, activestyle='none',
                               exportselection=False, width=56)
            barra = tk.Scrollbar(quadro, command=lista.yview)
            lista.configure(yscrollcommand=barra.set)
            barra.pack(side='right', fill='y')
            lista.pack(fill='both', expand=True, padx=12, pady=10)
            for instante, _, partida in registros:
                data = datetime.fromtimestamp(instante).strftime('%d/%m %H:%M')
                modo = 'Dois jogadores' if partida.modo == 'dupla' else f'Máquina, {partida.dificuldade.lower()}'
                situacao = 'terminada' if partida.estado.encerrada else f'{partida.jogadas} jogadas'
                a, b = partida.estado.placar
                lista.insert('end', f'  {data}     {modo}     {a} × {b}     {situacao}')

            def abrir():
                if lista.curselection():
                    self.iniciar(registros[lista.curselection()[0]][2])

            lista.bind('<Double-Button-1>', lambda _: abrir())
            lista.bind('<Return>', lambda _: abrir())
            lista.selection_set(0)
            lista.focus_set()
            self.botao(coluna, 'Abrir partida', abrir, principal=True).pack(anchor='w', pady=16)
        if erros:
            self.texto(f'{len(erros)} arquivo(s) não puderam ser lidos e foram ignorados. Eles continuam na pasta.',
                       12, ACAFRAO, pai=coluna)

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
        self.sob_mouse = None
        cabecalho = tk.Frame(self.conteudo, bg=FUNDO)
        cabecalho.pack(fill='x')
        self.titulo = tk.Label(cabecalho, font=(self.fonte, 26, 'bold'), fg=TEXTO, bg=FUNDO, anchor='w')
        self.titulo.pack(fill='x')
        self.mensagem = tk.StringVar()
        tk.Label(cabecalho, textvariable=self.mensagem, fg=SUAVE, bg=FUNDO, font=(self.fonte, 15),
                 wraplength=900, justify='left', anchor='nw', height=2).pack(fill='x', pady=(4, 0))
        self.tabuleiro = tk.Canvas(self.conteudo, bg=FUNDO, highlightthickness=0, height=380)
        self.tabuleiro.pack(fill='both', expand=True, pady=8)
        self.tabuleiro.bind('<Configure>', lambda _: self.desenhar_tabuleiro())
        self.tabuleiro.bind('<Button-1>', self.clicar_tabuleiro)
        self.tabuleiro.bind('<Motion>', self.passar_mouse)
        self.tabuleiro.bind('<Leave>', lambda _: self.passar_mouse(None))
        rodape = tk.Frame(self.conteudo, bg=FUNDO)
        rodape.pack(fill='x')
        tk.Label(rodape, text='Clique numa casa ou use as teclas 1 a 6, da esquerda para a direita.',
                 fg=SUAVE, bg=FUNDO, font=(self.fonte, 12)).pack(side='left')
        if tutorial:
            self.avancar_tutorial = self.botao(rodape, 'Próxima etapa', self.proxima_etapa, principal=True, tamanho=14)
            self.avancar_tutorial.pack(side='right')
            self.botao(rodape, 'Repetir', lambda: self.iniciar_tutorial(self.etapa), tamanho=14).pack(side='right', padx=8)
            self.status.set(f'Tutorial, etapa {self.etapa+1} de {len(ETAPAS)}. Nada aqui é salvo.')
        else:
            self.botao(rodape, 'Novo jogo', self.novo_jogo, tamanho=14).pack(side='right')
            self.salvar()
        self.mensagem.set(ETAPAS[self.etapa].instrucao if tutorial else
                          'Escolha uma casa sua com sementes. A joga na fileira de baixo; B, na de cima.')
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

    def jogavel(self, casa):
        if not self.pode_jogar() or casa not in casas_disponiveis(self.partida.estado):
            return False
        return self.etapa is None or casa == ETAPAS[self.etapa].casa

    def escolher_coluna(self, coluna):
        jogador = self.partida.estado.jogador_atual
        casas = CASAS[0] if jogador == 0 else tuple(reversed(CASAS[1]))
        self.selecionar_casa(casas[coluna])

    def casa_em(self, x, y):
        for posicao, (x1, y1, x2, y2) in self.areas.items():
            if x1 <= x <= x2 and y1 <= y <= y2:
                return posicao

    def clicar_tabuleiro(self, evento):
        casa = self.casa_em(evento.x, evento.y)
        if casa is not None and casa not in DEPOSITOS:
            self.selecionar_casa(casa)

    def passar_mouse(self, evento):
        casa = self.casa_em(evento.x, evento.y) if evento else None
        casa = casa if casa is not None and self.jogavel(casa) else None
        self.tabuleiro.configure(cursor='hand2' if casa is not None else '')
        if casa != self.sob_mouse:
            self.sob_mouse = casa
            self.desenhar_tabuleiro()

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
        jogador = self.nome_jogador(self.partida.estado.jogador_atual)
        resultado = self.partida.jogar(casa)
        self.animador.iniciar(resultado.eventos)
        self.sob_mouse = None
        self.resumo_jogada = f'{jogador} jogou P{casa}. '
        self.resumo_jogada += f'Capturou {resultado.capturadas} sementes. ' if resultado.capturadas else ''
        self.resumo_jogada += 'A última semente caiu no depósito: joga de novo.' if resultado.turno_extra else ''
        if self.etapa is None:
            self.salvar()
        self.atualizar_controles()

    def salvar(self):
        if not self.partida or self.etapa is not None:
            return
        try:
            self.arquivos.salvar(self.partida)
            self.status.set('Partida salva às ' + datetime.now().strftime('%H:%M:%S') + '.')
            self.erro_salvamento = False
        except OSError as erro:
            self.erro_salvamento = True
            self.status.set(f'Não foi possível salvar: {erro}')

    def iniciar_calculo(self):
        self.calculando = True
        self.cancelamento = threading.Event()
        cancelar, estado, geracao = self.cancelamento, self.partida.estado, self.geracao
        dificuldade = self.partida.dificuldade
        self.mensagem.set(f'A máquina ({dificuldade.lower()}) está pensando…')
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
                    mensagens = {'retirada': 'Sementes recolhidas da casa.',
                                 'distribuicao': f'Uma semente em P{evento.posicao}.',
                                 'captura': 'Captura! As sementes vão para o depósito.',
                                 'recolha': 'Um lado ficou vazio: as sobras vão para os depósitos.'}
                    self.mensagem.set(mensagens[evento.tipo] + f' Restam {evento.na_mao} na mão.')
                    if not self.animador.ativo:
                        self.tabuleiro_exibido = self.partida.estado.sementes
                        self.na_mao, self.destaque = 0, None
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
                            self.mensagem.set('A máquina não conseguiu jogar. Continue a partida pelos dois lados.')
                            self.partida.modo = 'dupla'
                            messagebox.showerror('Falha na máquina', erro + '\nA partida passou para dois jogadores.')
                            self.atualizar_controles()
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
            ultima = self.etapa == len(ETAPAS)-1
            self.avancar_tutorial.configurar(self.etapa_concluida, 'Concluir tutorial' if ultima else 'Próxima etapa')
        elif estado.encerrada and not self.animador.ativo:
            a, b = estado.placar
            titulo = 'Empate' if estado.vencedor is None else self.nome_jogador(estado.vencedor) + ' venceu'
            self.mensagem.set(f'Placar final: {a} a {b}. Todas as sementes foram para os depósitos.')
        elif self.animador.ativo:
            titulo = 'Semeando…'
        else:
            nome = self.nome_jogador(estado.jogador_atual)
            titulo = ('Vez da ' if nome == 'Máquina' else 'Vez do ') + nome
        self.titulo.configure(text=titulo)
        self.desenhar_tabuleiro()

    def desenhar_tabuleiro(self):
        if self.tela != 'partida':
            return
        canvas = self.tabuleiro
        canvas.delete('all')
        largura, altura = max(canvas.winfo_width(), 860), max(canvas.winfo_height(), 300)
        escala = min(largura / 1000, altura / 420)
        dx, dy = (largura-1000*escala)/2, (altura-420*escala)/2

        def p(x, y):
            return dx + x*escala, dy + y*escala

        def fonte(tamanho, peso='bold'):
            return (self.fonte, max(9, int(tamanho*escala)), peso)

        # Tábua com cantos arredondados e alguns veios.
        x1, y1, x2, y2, r = 10, 50, 990, 370, 70
        contorno = [(x1+r, y1), (x2-r, y1), (x2, y1), (x2, y1+r), (x2, y2-r), (x2, y2), (x2-r, y2),
                    (x1+r, y2), (x1, y2), (x1, y2-r), (x1, y1+r), (x1, y1)]
        canvas.create_polygon([c for ponto in contorno for c in p(*ponto)], smooth=True,
                              fill=MADEIRA, outline=MADEIRA_ESCURA, width=max(2, 3*escala))
        for veio in range(5):
            base = 78 + veio * 62
            linha = [c for x in range(60, 960, 60) for c in p(x, base + 7*math.sin(x/90 + veio*1.7))]
            canvas.create_line(linha, smooth=True, fill='#8c5630', width=max(1, 2*escala))

        pontos = {13: (30, 80, 122, 340), 7: (878, 80, 970, 340)}
        for coluna in range(6):
            x = 146 + coluna * 120
            pontos[CASAS[0][coluna]] = (x, 222, x+104, 326)
            pontos[tuple(reversed(CASAS[1]))[coluna]] = (x, 94, x+104, 198)
        self.areas = {}
        estado = self.partida.estado
        for posicao, limites in pontos.items():
            a1, b1 = p(*limites[:2])
            a2, b2 = p(*limites[2:])
            self.areas[posicao] = (a1, b1, a2, b2)
            recuo = 4 * escala
            canvas.create_oval(a1, b1, a2, b2, fill=SOMBRA, outline='')
            fundo = COVA_CLARA if posicao == self.sob_mouse else COVA
            canvas.create_oval(a1+recuo, b1+recuo, a2, b2, fill=fundo, outline='')
            if posicao == self.destaque:
                canvas.create_oval(a1-3*escala, b1-3*escala, a2+3*escala, b2+3*escala, outline=TEXTO, width=max(2, 3*escala))
            elif self.jogavel(posicao):
                canvas.create_oval(a1-2*escala, b1-2*escala, a2+2*escala, b2+2*escala, outline=ACAFRAO, width=max(2, 3*escala))
            self.desenhar_sementes(posicao, a1, b1, a2, b2, escala)
            if posicao not in DEPOSITOS:
                ty = b2 + 14*escala if posicao in CASAS[0] else b1 - 14*escala
                canvas.create_text((a1+a2)/2, ty, text=str(self.tabuleiro_exibido[posicao]), fill=TEXTO, font=fonte(15))

        # Nome e placar junto ao depósito de cada jogador.
        vez = None if estado.encerrada or self.animador.ativo else estado.jogador_atual
        for jogador, x, y, ancora in ((1, 30, 26, 'w'), (0, 970, 396, 'e')):
            total, nome = self.tabuleiro_exibido[DEPOSITOS[jogador]], self.nome_jogador(jogador)
            cor = CORES_JOGADORES[jogador] if vez in (None, jogador) else SUAVE
            texto = f'{nome}   {total}' if ancora == 'w' else f'{total}   {nome}'
            canvas.create_text(*p(x, y), text=texto, anchor=ancora, fill=cor, font=fonte(20 if vez == jogador else 17))
        if self.na_mao:
            canvas.create_text(*p(500, 396), text=f'{self.na_mao} na mão', fill=TEXTO, font=fonte(15, 'normal'))

    def desenhar_sementes(self, posicao, x1, y1, x2, y2, escala):
        valor = self.tabuleiro_exibido[posicao]
        cx, cy = (x1+x2)/2, (y1+y2)/2
        raio = 6.5 * escala
        for semente in range(valor):
            angulo = semente * 2.399963
            distancia = math.sqrt((semente+0.5)/max(valor, 1))
            x = cx + math.cos(angulo)*distancia*((x2-x1)/2 - raio*1.6)
            y = cy + math.sin(angulo)*distancia*((y2-y1)/2 - raio*1.6)
            cor = CORES_SEMENTES[(posicao*7 + semente*3) % len(CORES_SEMENTES)]
            self.tabuleiro.create_oval(x-raio, y-raio*0.85, x+raio, y+raio*0.85, fill=cor, outline=SOMBRA)
            self.tabuleiro.create_oval(x-raio*0.5, y-raio*0.55, x-raio*0.05, y-raio*0.2, fill='#f7efe0', outline='')

    def sair(self):
        self.salvar()
        if self.erro_salvamento and not messagebox.askyesno('Sair sem salvar?', 'O salvamento falhou. Deseja sair mesmo assim?'):
            return
        self.interromper_calculo()
        self.janela.after_cancel(self.temporizador)
        self.janela.destroy()
