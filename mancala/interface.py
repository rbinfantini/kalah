"""Janela e navegação. Regras, reprodução e armazenamento ficam em módulos próprios."""
from datetime import datetime
import logging
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from .aparencia import (FUNDO, PAPEL, TEXTO, SUAVE, LINHA, VERDE,
                        AMBAR, AZUL, ESCURO, configurar_tema, rotulo, botao, painel)
from .tabuleiro import Tabuleiro
from .animacao import AnimadorJogada
from .caminhos import pasta_dados
from .estrategia import escolher_jogada
from .partidas import ArquivoPartidas, Partida
from .regras import CASAS, DEPOSITOS, casas_disponiveis
from .tutorial import ETAPAS

ESPERA_MINIMA_MAQUINA = 5.0
RITMO_NORMAL = 0.8


class Aplicativo:
    """
    Controla a janela principal, a navegação entre telas e a lógica do jogo.

    Parameters
    ----------
    janela : tk.Tk
        Instância principal da interface.
    pasta_partidas : str or Path, optional
        Diretório usado para salvar e carregar partidas.
    """

    def __init__(self, janela, pasta_partidas=None):
        """
        Inicializa a aplicação e monta a interface padrão do jogo.

        Parameters
        ----------
        janela : tk.Tk
            Janela principal da aplicação.
        pasta_partidas : str or Path, optional
            Caminho do diretório de salvamento; usa o padrão quando não informado.

        Returns
        -------
        None
            Cria o estado inicial da interface e a tela de menu.
        """
        self.janela = janela
        janela.title('Mancala Só Joga')
        largura = min(1200, janela.winfo_screenwidth() - 70)
        altura = min(800, janela.winfo_screenheight() - 90)
        janela.geometry(f'{largura}x{altura}+20+20')
        janela.minsize(900, 640)
        janela.configure(bg=FUNDO)
        janela.protocol('WM_DELETE_WINDOW', self.sair)
        self.estilo = configurar_tema(janela)
        self.arquivos = ArquivoPartidas(pasta_partidas if pasta_partidas is not None else pasta_dados() / 'partidas_salvas')
        self.partida = None
        self.animador = AnimadorJogada()
        self.cancelamento = None
        self.respostas = queue.Queue()
        self.geracao = 0
        self.calculando = False
        self.liberar_jogada_maquina_em = 0.0
        self.tela = ''
        self.etapa = None
        self.etapa_concluida = False
        self.destaque = None
        self.na_mao = 0
        self.resumo_jogada = ''
        self.erro_salvamento = False
        self.velocidade = tk.StringVar(value='Normal')
        self.temporizador = None
        topo = tk.Frame(janela, bg=FUNDO)
        topo.pack(fill='x', padx=30, pady=(12, 8))
        marca = tk.Frame(topo, bg=FUNDO)
        marca.pack(side='left')
        rotulo(marca, 'mancala', 18, editorial=True, negrito=True).pack(side='left')
        rotulo(marca, '  /  SÓ JOGA', 10, cor=SUAVE, negrito=True).pack(side='left', pady=(8, 0))
        self.botao(topo, 'Sair', self.sair, estilo='Discreto.TButton').pack(side='right')
        self.botao_menu = self.botao(topo, 'Menu', self.menu, estilo='Discreto.TButton')
        self.botao_menu.pack(side='right', padx=6)
        self.botao_voltar = self.botao(topo, '← Voltar', self.voltar, estilo='Discreto.TButton')
        self.botao_voltar.pack(side='right')
        tk.Frame(janela, bg=LINHA, height=1).pack(fill='x', padx=30)
        rodape = tk.Frame(janela, bg=FUNDO)
        rodape.pack(side='bottom', fill='x', padx=30, pady=(8, 14))
        self.status = tk.StringVar(value='Pronto para jogar.')
        rotulo(rodape, textvariable=self.status, tamanho=9, cor=SUAVE).pack(side='left')
        rotulo(rodape, 'MANCALA  ·  SÓ JOGA', 9, cor=SUAVE).pack(side='right')
        self.conteudo = tk.Frame(janela, bg=FUNDO)
        self.conteudo.pack(fill='both', expand=True, padx=30, pady=(14, 4))
        janela.bind('<Escape>', lambda _: self.voltar())
        for numero in range(1, 7):
            janela.bind(str(numero), lambda e, c=numero-1: self.atalho_casa(e, c))
        self.ultimo_quadro = time.monotonic()
        self.menu()
        self.temporizador = janela.after(40, self.atualizar)

    def voltar(self):
        """
        Retorna para a tela anterior em fluxo de navegação.

        Returns
        -------
        None
            Alterna entre telas do menu, dificuldade e partida.
        """
        if self.tela == 'dificuldade':
            self.escolher_modo()
        elif self.tela != 'menu':
            self.menu()

    def atalho_casa(self, evento, coluna):
        """
        Seleciona uma casa pela tecla numérica do teclado.

        Parameters
        ----------
        evento : tk.Event
            Evento do teclado.
        coluna : int
            Índice da casa selecionada pela tecla.

        Returns
        -------
        str or None
            'break' para impedir o comportamento padrão ou None quando ignorado.
        """
        if self.tela != 'partida' or self.janela.grab_current() is not None:
            return
        if isinstance(evento.widget, (tk.Entry, ttk.Entry, ttk.Combobox)):
            return
        self.escolher_coluna(coluna)
        return 'break'

    def cabecalho(self, categoria, titulo, descricao):
        """
        Cria o cabeçalho padrão de uma tela de menu ou configuração.

        Parameters
        ----------
        categoria : str
            Nome da categoria da tela.
        titulo : str
            Título principal exibido.
        descricao : str
            Texto auxiliar do bloco.

        Returns
        -------
        None
            Monta os elementos visuais do cabeçalho.
        """
        rotulo(self.conteudo, categoria.upper(), 10, cor=VERDE, negrito=True).pack(anchor='w')
        rotulo(self.conteudo, titulo, 29, editorial=True).pack(anchor='w', pady=(8, 8))
        rotulo(self.conteudo, descricao, 11, cor=SUAVE).pack(anchor='w', pady=(0, 22))

    def cartao_opcao(self, pai, numero, titulo, descricao, acao, principal=False):
        """
        Cria um cartão de escolha para telas de menu ou modos de jogo.

        Parameters
        ----------
        pai : tk.Misc
            Container do cartão.
        numero : str
            Identificador exibido no topo do cartão.
        titulo : str
            Nome da opção.
        descricao : str
            Texto explicativo da alternativa.
        acao : callable
            Callback executado ao escolher a opção.
        principal : bool, optional
            Indica se a opção deve receber destaque principal.

        Returns
        -------
        tk.Frame
            Cartão montado e pronto para uso.
        """
        cartao = painel(pai, padx=24, pady=24)
        rotulo(cartao, numero, 11, cor=VERDE, negrito=True).pack(anchor='w')
        rotulo(cartao, titulo, 22, editorial=True).pack(anchor='w', pady=(18, 12))
        explicacao = rotulo(cartao, descricao, 12, cor=SUAVE, wraplength=300)
        explicacao.pack(fill='x', anchor='w')
        cartao.bind('<Configure>', lambda e: explicacao.configure(wraplength=max(120, e.width-52)))
        self.botao(cartao, 'Escolher  →', acao, principal).pack(side='bottom', fill='x', pady=(24, 0))
        return cartao

    def botao(self, pai, texto, acao, principal=False, estilo=None):
        """
        Encapsula a criação padrão de botões da interface.

        Parameters
        ----------
        pai : tk.Misc
            Contêiner do botão.
        texto : str
            Texto exibido.
        acao : callable
            Função chamada ao clicar.
        principal : bool, optional
            Destaca o botão como principal.
        estilo : str, optional
            Estilo ttk opcional.

        Returns
        -------
        ttk.Button
            Botão configurado com a aparência do projeto.
        """
        return botao(pai, texto, acao, principal, estilo)

    def texto(self, texto, tamanho=14, cor=TEXTO):
        """
        Adiciona um bloco de texto padrão à tela atual.

        Parameters
        ----------
        texto : str
            Conteúdo textual.
        tamanho : int, optional
            Tamanho da fonte.
        cor : str, optional
            Cor do texto.

        Returns
        -------
        tk.Label
            Controle de texto criado na área de conteúdo.
        """
        controle = rotulo(self.conteudo, texto, tamanho, cor, wraplength=850)
        controle.pack(anchor='w', pady=(0, 14))
        return controle

    def interromper_calculo(self):
        """
        Cancela o cálculo da jogada do computador em andamento.

        Returns
        -------
        None
            Atualiza a geração de busca e limpa a fila de resultados.
        """
        self.geracao += 1
        if self.cancelamento:
            self.cancelamento.set()
        self.calculando = False
        self.liberar_jogada_maquina_em = 0.0

    def limpar_tela(self, nome):
        """
        Remove os widgets da tela atual e prepara a próxima exibição.

        Parameters
        ----------
        nome : str
            Nome da nova tela ativa.

        Returns
        -------
        None
            Destrói os filhos do conteúdo e reseta os estados de tela.
        """
        if self.tela == 'partida' and nome != 'partida':
            self.salvar()
        self.interromper_calculo()
        self.animador = AnimadorJogada()
        self.tela = nome
        self.botao_voltar.configure(state='disabled' if nome == 'menu' else 'normal')
        self.botao_menu.configure(state='disabled' if nome == 'menu' else 'normal')
        for filho in self.conteudo.winfo_children():
            filho.destroy()

    def menu(self):
        """
        Monta a tela inicial principal com opções de jogo, carregamento e tutorial.

        Returns
        -------
        None
            Exibe a página do menu principal.
        """
        self.limpar_tela('menu')
        self.partida = None
        self.etapa = None
        corpo = tk.Frame(self.conteudo, bg=FUNDO)
        corpo.pack(fill='both', expand=True)
        corpo.columnconfigure(0, weight=4, uniform='menu')
        corpo.columnconfigure(1, weight=7, uniform='menu')
        corpo.rowconfigure(0, weight=1)
        esquerda = tk.Frame(corpo, bg=FUNDO)
        esquerda.grid(row=0, column=0, sticky='nsew', padx=(0, 28), pady=22)
        rotulo(esquerda, 'SEU TEMPO. SUA ESTRATÉGIA.', 9, cor=VERDE, negrito=True).pack(anchor='w')
        rotulo(esquerda, 'Só mais\numa partida.', 31, editorial=True).pack(anchor='w', pady=(20, 16))
        subtitulo = rotulo(esquerda, 'Um clássico para jogar junto\nou desafiar a máquina.',
                          11, cor=SUAVE, wraplength=340)
        subtitulo.pack(anchor='w', pady=(0, 24))
        esquerda.bind('<Configure>', lambda e: subtitulo.configure(wraplength=max(160,e.width-10)))
        jogar = self.botao(esquerda, 'Jogar   →', self.escolher_modo, True)
        jogar.pack(fill='x', pady=(0, 10), ipady=5)
        self.botao(esquerda, 'Carregar jogo', self.listar_partidas).pack(fill='x', pady=(0, 10))
        self.botao(esquerda, 'Aprender a jogar', lambda: self.iniciar_tutorial(0)).pack(fill='x')
        registros, _ = self.arquivos.listar()
        recente = next((p for _,_,p in registros if not p.estado.encerrada), None)
        if recente:
            self.botao(esquerda, 'Continuar última partida  →', lambda: self.iniciar(recente),
                       estilo='Discreto.TButton').pack(anchor='w', pady=(14,0))
        direita = tk.Frame(corpo, bg=ESCURO, padx=16, pady=24)
        direita.grid(row=0, column=1, sticky='nsew', pady=8)
        rotulo(direita, 'O TABULEIRO É SEU.', 9, cor=AMBAR, negrito=True).pack(anchor='center')
        previa = Tabuleiro(direita, bg=ESCURO, height=100)
        previa.pack(fill='both', expand=True, pady=(12,0))
        rotulo(direita, 'Semeie. Capture. Jogue de novo.', 17, editorial=True).pack(anchor='center')
        legenda = rotulo(direita, 'Guarde mais sementes no seu depósito para vencer.',
                         10, cor=SUAVE, wraplength=500)
        legenda.pack(anchor='center', pady=(10,4))
        direita.bind('<Configure>', lambda e: legenda.configure(wraplength=max(200,e.width-40)))
        self.status.set('Jogue no seu ritmo.')
        jogar.focus_set()

    def escolher_modo(self):
        """
        Exibe a tela de escolha do modo de partida.

        Returns
        -------
        None
            Mostra as opções de jogador × jogador e jogador × máquina.
        """
        self.limpar_tela('modo')
        self.cabecalho('01 / Nova partida', 'Quem senta do outro lado?',
                      'Escolha seu adversário. As regras são as mesmas para os dois lados.')
        grade = tk.Frame(self.conteudo, bg=FUNDO)
        grade.pack(fill='both', expand=True, pady=(0, 28))
        for i, (titulo, descricao, acao) in enumerate([
            ('Jogador × jogador', 'Compartilhem o tabuleiro. Cada pessoa joga com seis casas e seu próprio depósito.',
             lambda: self.iniciar(Partida())),
            ('Jogador × máquina', 'Pratique no seu ritmo ou encare uma busca mais profunda. Você escolhe a dificuldade.',
             self.escolher_dificuldade)]):
            grade.columnconfigure(i, weight=1, uniform='modo')
            self.cartao_opcao(grade, f'0{i+1}', titulo, descricao, acao, i == 0).grid(
                row=0, column=i, sticky='nsew', padx=(0, 16) if i == 0 else (0, 0))
        grade.rowconfigure(0, weight=1)
        self.status.set('Uma nova partida começa com quatro sementes em cada casa.')

    def escolher_dificuldade(self):
        """
        Exibe os níveis de dificuldade do computador.

        Returns
        -------
        None
            Monta as opções de dificuldade antes de iniciar a partida.
        """
        self.limpar_tela('dificuldade')
        self.cabecalho('02 / Contra a máquina', 'Encontre seu desafio.',
                      'Você começa na fileira de baixo.')
        grade = tk.Frame(self.conteudo, bg=FUNDO)
        grade.pack(fill='both', expand=True, pady=(0, 28))
        niveis = [('Fácil', 'Para descobrir', 'Escolhas variadas, sem antecipar suas respostas. Um espaço para experimentar.'),
                  ('Normal', 'Para praticar', 'Antecipa capturas e turnos extras. Uma boa companhia para ganhar experiência.'),
                  ('Difícil', 'Para se desafiar', 'Busca mais profunda, com até quatro segundos por jogada. Sem vantagens nas regras.')]
        for i, (nivel, titulo, descricao) in enumerate(niveis):
            grade.columnconfigure(i, weight=1, uniform='nivel')
            self.cartao_opcao(grade, nivel.upper(), titulo, descricao,
                              lambda n=nivel: self.iniciar(Partida('maquina', n)),
                              nivel == 'Normal').grid(row=0, column=i, sticky='nsew',
                                                     padx=(0, 14) if i < 2 else (0, 0))
        grade.rowconfigure(0, weight=1)
        self.status.set('Todos os níveis funcionam offline.')

    def listar_partidas(self):
        """
        Mostra a lista de partidas salvas para reabrir ou continuar.

        Returns
        -------
        None
            Exibe as partidas disponíveis em tela.
        """
        self.limpar_tela('carregar')
        self.cabecalho('Sua coleção', 'Volte à próxima jogada.',
                      'Salvamento automático a cada escolha. Suas partidas mais recentes aparecem primeiro.')
        registros, erros = self.arquivos.listar()
        if not registros:
            vazio = painel(self.conteudo, padx=32, pady=40)
            vazio.pack(fill='both', expand=True, pady=(0, 20))
            rotulo(vazio, 'O tabuleiro está esperando por você.', 24, editorial=True).pack(pady=(18, 12))
            rotulo(vazio, 'Comece uma partida e ela aparecerá aqui automaticamente.', 12, cor=SUAVE).pack()
            self.botao(vazio, 'Começar a jogar  →', self.escolher_modo, True).pack(pady=30)
        else:
            ferramentas = tk.Frame(self.conteudo, bg=FUNDO)
            ferramentas.pack(fill='x', pady=(0, 12))
            rotulo(ferramentas, f'{len(registros)} partidas', 10, cor=SUAVE).pack(side='left')
            filtro = tk.StringVar(value='Todas')
            escolha = ttk.Combobox(ferramentas, textvariable=filtro, state='readonly',
                                   values=('Todas', 'Em andamento', 'Concluídas'), width=18)
            escolha.pack(side='right')
            rotulo(ferramentas, 'Mostrar  ', 10, cor=SUAVE).pack(side='right')
            quadro = painel(self.conteudo)
            quadro.pack(fill='both', expand=True)
            lista = ttk.Treeview(quadro, columns=('data', 'modo', 'placar', 'jogadas', 'estado'),
                                 show='headings', selectmode='browse', height=3)
            for coluna, titulo, largura in [('data', 'ÚLTIMA VEZ', 175), ('modo', 'PARTIDA', 220),
                                            ('placar', 'PLACAR', 85), ('jogadas', 'JOGADAS', 90),
                                            ('estado', 'SITUAÇÃO', 150)]:
                lista.heading(coluna, text=titulo)
                lista.column(coluna, width=largura, minwidth=70, anchor='w' if coluna in ('data','modo','estado') else 'center')
            barra = ttk.Scrollbar(quadro, command=lista.yview)
            lista.configure(yscrollcommand=barra.set)
            barra.pack(side='right', fill='y')
            lista.pack(fill='both', expand=True)
            rodape = tk.Frame(self.conteudo, bg=FUNDO)
            rodape.pack(fill='x', pady=14)
            rotulo(rodape, 'Duplo clique ou Enter para abrir.', 10, cor=SUAVE).pack(side='left')
            def abrir():
                selecionados = lista.selection()
                if selecionados:
                    self.iniciar(registros[int(selecionados[0])][2])
            abrir_botao = self.botao(rodape, 'Abrir partida  →', abrir, True)
            abrir_botao.pack(side='right')
            def preencher(_=None):
                for item in lista.get_children():
                    lista.delete(item)
                for indice, (instante, _, partida) in enumerate(registros):
                    situacao = 'Concluídas' if partida.estado.encerrada else 'Em andamento'
                    if filtro.get() not in ('Todas', situacao):
                        continue
                    a, b = partida.estado.placar
                    lista.insert('', 'end', iid=str(indice), values=(
                        datetime.fromtimestamp(instante).strftime('%d/%m/%Y  %H:%M'),
                        'Dois jogadores' if partida.modo == 'dupla' else f'Máquina · {partida.dificuldade}',
                        f'{a} × {b}', partida.jogadas, 'Concluída' if partida.estado.encerrada else situacao))
                itens = lista.get_children()
                abrir_botao.configure(state='normal' if itens else 'disabled')
                if itens:
                    lista.selection_set(itens[0])
                    lista.focus(itens[0])
            escolha.bind('<<ComboboxSelected>>', preencher)
            lista.bind('<Double-Button-1>', lambda _: abrir())
            lista.bind('<Return>', lambda _: abrir())
            preencher()
            lista.focus_set()
        if erros:
            rotulo(self.conteudo, f'{len(erros)} arquivo(s) não puderam ser lidos. Os originais foram preservados.',
                   10, cor=AMBAR).pack(anchor='w')
        self.status.set('Partidas guardadas neste computador.')

    def iniciar_tutorial(self, indice):
        """
        Inicia uma etapa específica do tutorial.

        Parameters
        ----------
        indice : int
            Índice da etapa no conjunto de exercícios.

        Returns
        -------
        None
            Carrega a partida de tutorial correspondente.
        """
        self.etapa = indice
        self.etapa_concluida = False
        self.iniciar(Partida(estado=ETAPAS[indice].estado), tutorial=True)

    def iniciar(self, partida, tutorial=False):
        """
        Inicia uma partida em tela e prepara o tabuleiro e os controles.

        Parameters
        ----------
        partida : Partida
            Partida a ser exibida.
        tutorial : bool, optional
            Indica se a partida é um tutorial guiado.

        Returns
        -------
        None
            Exibe o tabuleiro e configura o estado de interação.
        """
        self.limpar_tela('partida')
        if not tutorial:
            self.etapa = None
        self.partida = partida
        self.tabuleiro_exibido = partida.estado.sementes
        self.na_mao = 0
        self.destaque = None
        self.jogador_animacao = partida.estado.jogador_atual
        self.mensagem = tk.StringVar()
        self.contexto = tk.StringVar()
        placares = tk.Frame(self.conteudo, bg=FUNDO)
        placares.pack(fill='x', pady=(0,8))
        placares.columnconfigure(0, weight=1, uniform='ponta')
        placares.columnconfigure(1, weight=2)
        placares.columnconfigure(2, weight=1, uniform='ponta')
        centro = tk.Frame(placares, bg=FUNDO)
        centro.grid(row=0, column=1, sticky='nsew', padx=12)
        rotulo(centro, textvariable=self.contexto, tamanho=8, cor=SUAVE).pack(anchor='center', pady=(4,5))
        self.titulo = rotulo(centro, tamanho=16, editorial=True, wraplength=360)
        self.titulo.pack(anchor='center')
        self.placares = []
        for jogador in range(2):
            cartao = painel(placares, padx=14, pady=9)
            cartao.grid(row=0, column=2 if jogador==0 else 0, sticky='nsew')
            lado = tk.Frame(cartao, bg=PAPEL)
            lado.pack(side='left')
            nome = rotulo(lado, self.nome_jogador(jogador), 11, negrito=True)
            nome.pack(anchor='w')
            detalhe = rotulo(lado, '', 8, cor=SUAVE)
            detalhe.pack(anchor='w', pady=(4,0))
            pontos = rotulo(cartao, '0', 27, editorial=True)
            pontos.pack(side='right', padx=(10,0))
            self.placares.append((cartao,lado,nome,detalhe,pontos))
        self.tabuleiro = Tabuleiro(self.conteudo, self.selecionar_casa, height=150)
        self.tabuleiro.pack(fill='both', expand=True, pady=(2,8))
        aviso = painel(self.conteudo, padx=16, pady=10)
        aviso.pack(fill='x', pady=(0,10))
        self.indicador = rotulo(aviso, '', 9, cor=VERDE, negrito=True)
        self.indicador.pack(anchor='w')
        mensagem = rotulo(aviso, textvariable=self.mensagem, tamanho=11, wraplength=1020)
        mensagem.pack(fill='x', pady=(4,0))
        aviso.bind('<Configure>', lambda e: mensagem.configure(wraplength=max(200,e.width-36)))
        rodape = tk.Frame(self.conteudo, bg=FUNDO)
        rodape.pack(fill='x')
        rotulo(rodape, 'Animação  ', 9, cor=SUAVE).pack(side='left')
        ttk.Combobox(rodape, textvariable=self.velocidade, state='readonly', width=13,
                     values=('Normal','Rápido','Sem animação')).pack(side='left')
        if tutorial:
            self.avancar_tutorial = self.botao(rodape, 'Próxima etapa →', self.proxima_etapa, True)
            self.avancar_tutorial.pack(side='right')
            self.botao(rodape, 'Repetir', lambda: self.iniciar_tutorial(self.etapa),
                       estilo='Discreto.TButton').pack(side='right', padx=8)
            self.status.set('Aprenda jogando · acompanhe a casa iluminada.')
        else:
            self.botao(rodape, 'Nova partida', self.escolher_modo).pack(side='right')
            self.salvar()
        self.mensagem.set(ETAPAS[self.etapa].instrucao if tutorial else
                          'Escolha uma das casas iluminadas na sua fileira.')
        self.atualizar_controles()
        self.tabuleiro.focus_set()

    def proxima_etapa(self):
        """
        Avança para a próxima etapa do tutorial quando a atual foi concluída.

        Returns
        -------
        None
            Carrega a próxima etapa ou retorna ao menu ao fim.
        """
        if self.etapa_concluida:
            if self.etapa + 1 < len(ETAPAS):
                self.iniciar_tutorial(self.etapa + 1)
            else:
                self.menu()

    def nome_jogador(self, jogador):
        """
        Retorna o nome exibido do jogador associado ao índice.

        Parameters
        ----------
        jogador : int
            Índice do jogador, 0 ou 1.

        Returns
        -------
        str
            Nome amigável usado na interface.
        """
        if self.partida.modo == 'maquina':
            return 'Você' if jogador == 0 else 'Computador'
        return 'Jogador 1' if jogador == 0 else 'Jogador 2'

    def pode_jogar(self):
        """
        Verifica se a interface está liberada para receber uma jogada humana.

        Returns
        -------
        bool
            True quando é possível escolher uma casa no atual estado da partida.
        """
        return (self.tela == 'partida' and self.partida is not None
                and not self.animador.ativo and not self.calculando and not self.partida.estado.encerrada
                and not (self.partida.modo == 'maquina' and self.partida.estado.jogador_atual == 1)
                and not (self.etapa is not None and self.etapa_concluida))

    def casas_jogaveis(self):
        """
        Retorna as casas válidas para a jogada atual, respeitando o tutorial.

        Returns
        -------
        tuple[int, ...]
            Casas jogáveis permitidas pela interface.
        """
        if not self.pode_jogar():
            return ()
        casas = casas_disponiveis(self.partida.estado)
        return tuple(casa for casa in casas if self.etapa is None or casa == ETAPAS[self.etapa].casa)

    def escolher_coluna(self, coluna):
        """
        Seleciona uma casa usando a coluna da interface numérica.

        Parameters
        ----------
        coluna : int
            Índice da coluna escolhida.

        Returns
        -------
        None
            Chama a jogada correspondente quando o turno permite.
        """
        if not self.pode_jogar():
            return
        jogador = self.partida.estado.jogador_atual
        casas = CASAS[0] if jogador == 0 else tuple(reversed(CASAS[1]))
        self.selecionar_casa(casas[coluna])

    def clicar_tabuleiro(self, evento):
        """
        Encaminha o clique do mouse para o canvas do tabuleiro.

        Parameters
        ----------
        evento : tk.Event
            Evento de clique recebido pela interface.

        Returns
        -------
        None
            Delegua a seleção ao componente gráfico.
        """
        self.tabuleiro.clicar(evento)

    def selecionar_casa(self, casa):
        """
        Tenta executar a jogada escolhida na casa informada.

        Parameters
        ----------
        casa : int
            Casa selecionada pelo jogador.

        Returns
        -------
        None
            Executa a jogada ou atualiza a mensagem de erro.
        """
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
        """
        Executa a jogada e inicia a animação do resultado.

        Parameters
        ----------
        casa : int
            Casa escolhida para a jogada.

        Returns
        -------
        None
            Atualiza o estado visual e salva a partida quando necessário.
        """
        self.jogador_animacao = self.partida.estado.jogador_atual
        jogador = self.nome_jogador(self.jogador_animacao)
        resultado = self.partida.jogar(casa)
        self.animador.iniciar(resultado.eventos)
        self.resumo_jogada = f'{jogador} distribuiu as sementes. '
        if resultado.capturadas:
            self.resumo_jogada += f'Capturou {resultado.capturadas} sementes. '
        self.resumo_jogada += 'Última semente no depósito: jogue novamente.' if resultado.turno_extra else 'Jogada concluída.'
        if self.etapa is None:
            self.salvar()
        self.atualizar_controles()

    def salvar(self):
        """
        Salva a partida atual em disco quando a sessão permite.

        Returns
        -------
        None
            Atualiza o status e marca erro de gravação quando necessário.
        """
        if not self.partida or self.etapa is not None:
            return
        try:
            self.arquivos.salvar(self.partida)
            self.status.set('Partida salva · ' + datetime.now().strftime('%H:%M:%S') + '')
            self.erro_salvamento = False
        except OSError as erro:
            self.erro_salvamento = True
            self.status.set(f'Não foi possível salvar: {erro}')

    def iniciar_calculo(self):
        """
        Dispara a busca da jogada do computador em thread separada.

        Returns
        -------
        None
            Inicia o cálculo assíncrono da estratégia.
        """
        self.calculando = True
        self.liberar_jogada_maquina_em = time.monotonic() + ESPERA_MINIMA_MAQUINA
        self.cancelamento = threading.Event()
        cancelar, estado, geracao = self.cancelamento, self.partida.estado, self.geracao
        dificuldade = self.partida.dificuldade
        self.mensagem.set(f'O computador está escolhendo sua jogada. Dificuldade: {dificuldade.lower()}.')
        self.atualizar_controles()

        def calcular():
            try:
                resposta = escolher_jogada(estado, dificuldade, cancelar)
                self.respostas.put((geracao, resposta, None))
            except Exception as erro:
                logging.exception('Falha na busca do computador')
                self.respostas.put((geracao, None, str(erro)))

        threading.Thread(target=calcular, daemon=True, name='estrategia-mancala').start()

    def receber_jogada_maquina(self, agora):
        """
        Processa a resposta da busca do computador quando ela ficou pronta.

        Parameters
        ----------
        agora : float
            Timestamp atual do relógio da aplicação.

        Returns
        -------
        None
            Executa a jogada calculada ou informa falha no cálculo.
        """
        if agora < self.liberar_jogada_maquina_em:
            return
        try:
            geracao, resposta, erro = self.respostas.get_nowait()
            if geracao == self.geracao:
                self.calculando = False
                if erro:
                    self.mensagem.set('Cálculo interrompido. Retome esta partida pelo menu para tentar novamente.')
                    self.partida.modo = 'dupla'
                    messagebox.showerror('Falha no computador', erro + '\nA partida passou para controle humano.', parent=self.janela)
                    self.atualizar_controles()
                else:
                    self.executar_jogada(resposta.casa)
        except queue.Empty:
            pass

    def atualizar(self):
        """
        Atualiza a tela, a animação e a busca da máquina em uma iteração do loop.

        Returns
        -------
        None
            Reagenda a próxima chamada do timer da interface.
        """
        agora = time.monotonic()
        decorrido = min(agora - self.ultimo_quadro, 0.2)
        self.ultimo_quadro = agora
        if self.tela == 'partida':
            if self.animador.ativo:
                ritmo = self.velocidade.get()
                if ritmo == 'Sem animação':
                    # Consome eventos sem alterar a resolução da jogada.
                    evento = None
                    while self.animador.ativo:
                        evento = self.animador.avancar(10)
                else:
                    evento = self.animador.avancar(decorrido * (2.5 if ritmo == 'Rápido' else RITMO_NORMAL))
                if evento:
                    self.tabuleiro_exibido = evento.sementes
                    self.na_mao, self.destaque = evento.na_mao, evento.posicao
                    mensagens = {'retirada': 'Sementes retiradas da casa escolhida.',
                                 'distribuicao': 'Uma semente em cada casa.',
                                 'captura': 'Captura: sementes transferidas para o depósito.',
                                 'recolha': 'Lado vazio: recolhendo as sementes restantes.'}
                    self.mensagem.set(mensagens[evento.tipo] + f' Na mão: {evento.na_mao}.')
                    if not self.animador.ativo:
                        self.tabuleiro_exibido = self.partida.estado.sementes
                        self.na_mao, self.destaque = 0, None
                        self.mensagem.set(self.resumo_jogada)
                        if self.etapa is not None:
                            self.etapa_concluida = True
                            self.mensagem.set(ETAPAS[self.etapa].conclusao)
                    self.atualizar_controles()
            elif self.calculando:
                self.receber_jogada_maquina(agora)
            elif (self.partida.modo == 'maquina' and self.partida.estado.jogador_atual == 1
                  and not self.partida.estado.encerrada):
                self.iniciar_calculo()
        self.temporizador = self.janela.after(40, self.atualizar)

    def atualizar_controles(self):
        """
        Recalcula textos, destaques e pontuação exibida no tabuleiro.

        Returns
        -------
        None
            Atualiza os widgets visuais da partida ativa.
        """
        estado = self.partida.estado
        fim = estado.encerrada and not self.animador.ativo
        if self.etapa is not None:
            titulo = ETAPAS[self.etapa].titulo.split(' · ',1)[-1]
            self.contexto.set(f'APRENDER A JOGAR  ·  {self.etapa+1} / {len(ETAPAS)}')
            self.avancar_tutorial.configure(state='normal' if self.etapa_concluida else 'disabled',
                                            text='Concluir tutorial' if self.etapa == len(ETAPAS)-1 else 'Próxima etapa →')
        else:
            self.contexto.set('DOIS JOGADORES' if self.partida.modo == 'dupla' else f'CONTRA O COMPUTADOR · {self.partida.dificuldade.upper()}')
            if fim:
                titulo = 'Empate!' if estado.vencedor is None else self.nome_jogador(estado.vencedor)+' venceu!'
                self.mensagem.set(f'Fim de jogo. Placar: {estado.placar[0]} a {estado.placar[1]}. Que tal mais uma?')
            elif self.animador.ativo:
                titulo = 'Semeando…'
            elif self.calculando:
                titulo = 'Pensando…'
            else:
                titulo = 'Sua vez' if self.partida.modo == 'maquina' else 'Vez do '+self.nome_jogador(estado.jogador_atual)
        self.titulo.configure(text=titulo)
        self.indicador.configure(text='MUITO BEM!' if self.etapa is not None and self.etapa_concluida else
                                 'PARTIDA ENCERRADA' if fim else 'DISTRIBUINDO AS SEMENTES' if self.animador.ativo else
                                 'SEU ADVERSÁRIO ESTÁ PENSANDO' if self.calculando else 'SUA PRÓXIMA JOGADA')
        vez = self.jogador_animacao if self.animador.ativo else estado.jogador_atual
        for jogador, (cartao,lado,nome,detalhe,pontos) in enumerate(self.placares):
            ativo = not fim and jogador == vez
            cor = VERDE if jogador == 0 else AZUL
            cartao.configure(highlightbackground=cor if ativo else LINHA)
            nome.configure(text=self.nome_jogador(jogador), fg=cor)
            pontos.configure(text=str(self.tabuleiro_exibido[DEPOSITOS[jogador]]), fg=TEXTO)
            detalhe.configure(text=('Sua vez · ' if ativo else '') +
                              ('Fileira de baixo' if jogador==0 else 'Fileira de cima'))
        self.desenhar_tabuleiro()

    def desenhar_tabuleiro(self):
        """
        Redesenha o tabuleiro atual com casas jogáveis e destaques.

        Returns
        -------
        None
            Atualiza o componente Tabuleiro com o estado recente.
        """
        if self.tela == 'partida':
            self.tabuleiro.atualizar(self.tabuleiro_exibido, self.casas_jogaveis(), self.destaque)

    def sair(self):
        """
        Finaliza a aplicação com confirmação de salvamento, quando necessário.

        Returns
        -------
        None
            Fecha a janela ou mantém a aplicação aberta em caso de falha de gravação.
        """
        self.salvar()
        if self.erro_salvamento and not messagebox.askyesno(
                'Sair sem salvar?', 'O salvamento falhou. Deseja sair mesmo assim?', parent=self.janela):
            return
        self.interromper_calculo()
        if self.temporizador is not None:
            self.janela.after_cancel(self.temporizador)
        self.janela.destroy()
