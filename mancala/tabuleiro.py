"""Canvas do tabuleiro: desenha e recebe entradas; não aplica regras do jogo."""
import math
import tkinter as tk
from PIL import ImageTk
from .aparencia import FUNDO, TEXTO, SUAVE
from .regras import CASAS, DEPOSITOS
from .graficos import limites_casas, renderizar_tabuleiro, renderizar_anel, renderizar_semente


def dentro_da_casa(x, y, limites):
    """
    Verifica se um ponto pertence à área elíptica de uma casa.

    Parameters
    ----------
    x : float
        Coordenada x do clique.
    y : float
        Coordenada y do clique.
    limites : tuple
        Retângulo que envolve a casa.

    Returns
    -------
    bool
        True quando o ponto cai dentro da forma elíptica da casa.
    """
    x1, y1, x2, y2 = limites
    return ((x - (x1+x2)/2) / ((x2-x1)/2))**2 + ((y - (y1+y2)/2) / ((y2-y1)/2))**2 <= 1


class Tabuleiro(tk.Canvas):
    """
    Canvas especializado em renderizar e interagir com o tabuleiro do jogo.

    Parameters
    ----------
    pai : tk.Misc
        Container onde o widget será anexado.
    escolher : callable, optional
        Callback usado ao confirmar uma casa.
    **opcoes
        Opções adicionais para o Canvas Tk.
    """

    def __init__(self, pai, escolher=None, **opcoes):
        """
        Inicializa o canvas com eventos de interface e estado interno do tabuleiro.

        Parameters
        ----------
        pai : tk.Misc
            Container do widget.
        escolher : callable, optional
            Função chamada quando uma casa é selecionada.
        **opcoes
            Atributos extras do Canvas.
        """
        self.cor_rotulos = opcoes.pop('cor_rotulos', SUAVE)
        super().__init__(pai, bg=opcoes.pop('bg', FUNDO), highlightthickness=0,
                         takefocus=bool(escolher), **opcoes)
        self.imagens = {}
        self.largura_imagem = None
        self.escolher = escolher
        self.sementes = (4, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 0)
        self.disponiveis = ()
        self.destaque = self.sobre = self.foco = None
        self.areas = {}
        self.bind('<Configure>', lambda _: self.desenhar())
        self.bind('<Motion>', self.mover_mouse)
        self.bind('<Leave>', self.sair_mouse)
        self.bind('<Button-1>', self.clicar)
        self.bind('<FocusIn>', self.receber_foco)
        self.bind('<FocusOut>', lambda _: self.desenhar())
        self.bind('<Left>', lambda _: self.mover_foco(-1))
        self.bind('<Right>', lambda _: self.mover_foco(1))
        self.bind('<Return>', self.confirmar)
        self.bind('<space>', self.confirmar)

    def atualizar(self, sementes, disponiveis=(), destaque=None):
        """
        Atualiza o estado visual do tabuleiro e as casas disponíveis.

        Parameters
        ----------
        sementes : tuple[int, ...]
            Total de sementes em cada posição.
        disponiveis : tuple[int, ...], optional
            Casas válidas para a jogada atual.
        destaque : int, optional
            Casa destacada na animação.

        Returns
        -------
        None
            Redesenha o tabuleiro com o novo estado.

        Notes
        -----
        sementes pode ser um quadro intermediário da animação. O chamador
        fornece as casas disponíveis; este Canvas não decide turnos, capturas
        ou o fim da partida.
        """
        self.sementes = sementes
        self.disponiveis = tuple(disponiveis)
        self.destaque = destaque
        if self.sobre not in self.disponiveis:
            self.sobre = None
        if self.foco not in self.disponiveis:
            self.foco = self.disponiveis[0] if self.disponiveis else None
        self.configure(cursor='hand2' if self.sobre is not None else '')
        self.desenhar()

    def casa_em(self, x, y):
        """
        Converte coordenadas do mouse em uma casa do tabuleiro.

        Parameters
        ----------
        x : float
            Posição x do cursor.
        y : float
            Posição y do cursor.

        Returns
        -------
        int or None
            Casa sob o ponteiro ou None quando não está em nenhuma área válida.
        """
        return next((p for p, area in self.areas.items() if dentro_da_casa(x, y, area)), None)

    def mover_mouse(self, evento):
        """
        Atualiza o estado de hover quando o mouse move sobre o tabuleiro.

        Parameters
        ----------
        evento : tk.Event
            Evento do mouse.

        Returns
        -------
        None
            Redesenha a interface com o novo hover.
        """
        casa = self.casa_em(evento.x, evento.y)
        sobre = casa if casa in self.disponiveis else None
        if sobre != self.sobre:
            self.sobre = sobre
            self.configure(cursor='hand2' if sobre is not None else '')
            self.desenhar()

    def sair_mouse(self, _):
        """
        Limpa o destaque do mouse ao sair da área do tabuleiro.

        Parameters
        ----------
        _ : object
            Evento ignorado.

        Returns
        -------
        None
            Remove o estado de hover.
        """
        if self.sobre is not None:
            self.sobre = None
            self.configure(cursor='')
            self.desenhar()

    def clicar(self, evento):
        """
        Trata clique do usuário para selecionar uma casa jogável.

        Parameters
        ----------
        evento : tk.Event
            Evento de clique do mouse.

        Returns
        -------
        None
            Chama o callback de seleção quando a casa é válida.
        """
        casa = self.casa_em(evento.x, evento.y)
        if casa in self.disponiveis and self.escolher:
            self.foco = casa
            self.focus_set()
            self.escolher(casa)

    def receber_foco(self, _):
        """
        Ajusta o foco de teclado ao receber atenção do canvas.

        Parameters
        ----------
        _ : object
            Evento ignorado.

        Returns
        -------
        None
            Define a casa inicial do foco, se necessário.
        """
        if self.foco is None and self.disponiveis:
            self.foco = self.disponiveis[0]
        self.desenhar()

    def mover_foco(self, passo):
        """
        Move o foco de teclado entre as casas disponíveis.

        Parameters
        ----------
        passo : int
            Deslocamento do foco no conjunto de casas válidas.

        Returns
        -------
        str
            Sempre 'break' para evitar o avanço do comportamento padrão.
        """
        casas = sorted(self.disponiveis, key=lambda p: self.areas.get(p, (0,))[0])
        if casas:
            atual = casas.index(self.foco) if self.foco in casas else 0
            self.foco = casas[(atual + passo) % len(casas)]
            self.desenhar()
        return 'break'

    def confirmar(self, _):
        """
        Confirma a casa em foco por teclado.

        Parameters
        ----------
        _ : object
            Evento ignorado.

        Returns
        -------
        str
            Sempre 'break' para bloquear o comportamento padrão do teclado.
        """
        if self.foco in self.disponiveis and self.escolher:
            self.escolher(self.foco)
        return 'break'

    def imagem(self, tipo, tamanho, cor=0):
        """
        Gera ou reutiliza uma imagem Tk para o tipo e tamanho solicitados.

        Parameters
        ----------
        tipo : str
            Tipo de imagem: tabuleiro, semente ou anel.
        tamanho : int
            Tamanho alvo da imagem.
        cor : int, optional
            Índice da cor, quando a imagem é uma semente.

        Returns
        -------
        ImageTk.PhotoImage
            Imagem mantida em cache para o canvas.

        Notes
        -----
        O Canvas precisa manter referências Python às PhotoImages enquanto
        as exibe. Este cache local é diferente do cache Pillow compartilhado
        por graficos.py; é liberado ao mudar de tamanho ou destruir a tela.
        """
        chave = (tipo, tamanho, cor)
        if chave not in self.imagens:
            if tipo == 'tabuleiro':
                desenho = renderizar_tabuleiro(tamanho)
            elif tipo == 'semente':
                desenho = renderizar_semente(cor, tamanho)
            else:
                desenho = renderizar_anel(tipo, tamanho)
            self.imagens[chave] = ImageTk.PhotoImage(desenho, master=self)
        return self.imagens[chave]

    def destroy(self):
        """
        Libera as imagens em cache antes de destruir o canvas.

        Returns
        -------
        None
            Remove referências de PhotoImage e encerra o widget.
        """
        self.delete('all')
        self.imagens.clear()
        super().destroy()

    def desenhar(self):
        """
        Redesenha o tabuleiro inteiro com o estado atual de sementes e destaques.

        Returns
        -------
        None
            Atualiza o conteúdo visual do canvas.
        """
        self.delete('all')
        largura, altura = self.winfo_width(), self.winfo_height()
        if largura < 20 or altura < 20:
            return
        disponivel = min(largura-8, (altura-8)*3, 1600)
        tamanho = max(360, int(disponivel//40)*40)
        # Uma só escala para ambos os eixos mantém todas as casas circulares.
        escala = tamanho/1200
        dx, dy = (largura-tamanho)/2, (altura-tamanho/3)/2
        if tamanho != self.largura_imagem:
            self.imagens.clear()
            self.largura_imagem = tamanho
        self.create_image(largura/2, altura/2, image=self.imagem('tabuleiro', tamanho))
        areas = limites_casas()
        self.areas = {}
        for posicao, (x1,y1,x2,y2) in areas.items():
            self.areas[posicao] = (dx+x1*escala, dy+y1*escala, dx+x2*escala, dy+y2*escala)
            cx, cy = (x1+x2)/2, (y1+y2)/2
            ativa = posicao in self.disponiveis
            if posicao not in DEPOSITOS:
                anel = 'destaque' if posicao == self.destaque else 'foco' if (
                    posicao == self.sobre or self.focus_get() == self and posicao == self.foco
                ) else 'ativa' if ativa else None
                if anel:
                    self.create_image(dx+cx*escala, dy+cy*escala,
                                      image=self.imagem(anel, tamanho))
            quantidade = self.sementes[posicao]
            raio = min(14, 43 / math.sqrt(max(1, quantidade)))
            tamanho_semente = max(6, min(30, round(raio*2*escala/2)*2))
            for indice in range(quantidade):
                # Ângulo áureo e raio pela raiz distribuem sementes sem sorteios
                # que mudariam suas posições a cada redesenho.
                angulo = indice * 2.399963
                distancia = math.sqrt((indice+.5)/max(quantidade,1))
                x = cx + math.cos(angulo)*distancia*((x2-x1)/2-raio-13)
                y = cy + math.sin(angulo)*distancia*((y2-y1)/2-raio-13)
                self.create_image(dx+x*escala, dy+y*escala,
                    image=self.imagem('semente', tamanho_semente, (indice+posicao)%4))
            ynumero = 354 if posicao in DEPOSITOS else 191 if posicao in CASAS[1] else 365
            self.create_text(dx+cx*escala, dy+ynumero*escala, text=str(quantidade),
                             fill='#f2dbc0' if posicao in DEPOSITOS else '#b1dfd4' if ativa else '#d1c4b6',
                             font=('Segoe UI', -max(12, round((24 if posicao in DEPOSITOS else 19)*escala)), 'bold'))
