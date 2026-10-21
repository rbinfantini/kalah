"""Canvas do tabuleiro: desenha e recebe entradas; não aplica regras do jogo."""
import math
import tkinter as tk
from pathlib import Path
from .aparencia import FUNDO, TEXTO, SUAVE
from .regras import CASAS, DEPOSITOS

RECURSOS = Path(__file__).resolve().parent / 'recursos'


def dentro_da_casa(x, y, limites):
    """A área clicável acompanha a cavidade elíptica, sem cantos invisíveis."""
    x1, y1, x2, y2 = limites
    return ((x - (x1+x2)/2) / ((x2-x1)/2))**2 + ((y - (y1+y2)/2) / ((y2-y1)/2))**2 <= 1


class Tabuleiro(tk.Canvas):
    def __init__(self, pai, escolher=None, **opcoes):
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
        return next((p for p, area in self.areas.items() if dentro_da_casa(x, y, area)), None)

    def mover_mouse(self, evento):
        casa = self.casa_em(evento.x, evento.y)
        sobre = casa if casa in self.disponiveis else None
        if sobre != self.sobre:
            self.sobre = sobre
            self.configure(cursor='hand2' if sobre is not None else '')
            self.desenhar()

    def sair_mouse(self, _):
        if self.sobre is not None:
            self.sobre = None
            self.configure(cursor='')
            self.desenhar()

    def clicar(self, evento):
        casa = self.casa_em(evento.x, evento.y)
        if casa in self.disponiveis and self.escolher:
            self.foco = casa
            self.focus_set()
            self.escolher(casa)

    def receber_foco(self, _):
        if self.foco is None and self.disponiveis:
            self.foco = self.disponiveis[0]
        self.desenhar()

    def mover_foco(self, passo):
        casas = sorted(self.disponiveis, key=lambda p: self.areas.get(p, (0,))[0])
        if casas:
            atual = casas.index(self.foco) if self.foco in casas else 0
            self.foco = casas[(atual + passo) % len(casas)]
            self.desenhar()
        return 'break'

    def confirmar(self, _):
        if self.foco in self.disponiveis and self.escolher:
            self.escolher(self.foco)
        return 'break'

    def imagem(self, nome):
        if nome not in self.imagens:
            self.imagens[nome] = tk.PhotoImage(master=self, file=str(RECURSOS / nome))
        return self.imagens[nome]

    def desenhar(self):
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
        self.create_image(largura/2, altura/2, image=self.imagem(f'tabuleiro-{tamanho}.png'))
        areas = {13: (35,65,135,335), 7: (1065,65,1165,335)}
        for coluna, superior in enumerate(reversed(CASAS[1])):
            x = 169 + coluna*148
            areas[superior] = (x,48,x+122,170)
            areas[coluna] = (x,222,x+122,344)
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
                                      image=self.imagem(f'{anel}-{tamanho}.png'))
            quantidade = self.sementes[posicao]
            raio = min(14, 43 / math.sqrt(max(1, quantidade)))
            tamanho_semente = max(6, min(30, round(raio*2*escala/2)*2))
            for indice in range(quantidade):
                angulo = indice * 2.399963
                distancia = math.sqrt((indice+.5)/max(quantidade,1))
                x = cx + math.cos(angulo)*distancia*((x2-x1)/2-raio-13)
                y = cy + math.sin(angulo)*distancia*((y2-y1)/2-raio-13)
                self.create_image(dx+x*escala, dy+y*escala,
                    image=self.imagem(f'semente-{(indice+posicao)%4}-{tamanho_semente}.png'))
            ynumero = 354 if posicao in DEPOSITOS else 191 if posicao in CASAS[1] else 365
            self.create_text(dx+cx*escala, dy+ynumero*escala, text=str(quantidade),
                             fill='#f2dbc0' if posicao in DEPOSITOS else '#b1dfd4' if ativa else '#d1c4b6',
                             font=('Segoe UI', -max(12, round((24 if posicao in DEPOSITOS else 19)*escala)), 'bold'))
