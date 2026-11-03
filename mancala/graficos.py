"""Desenhos procedurais com Pillow, sem arquivos de imagem ou acesso ao disco.

O original em alta resolução e os caches limitados são compartilhados entre
telas. As imagens retornadas são somente para leitura; PhotoImage pertence
ao Canvas que a exibe, nunca a este módulo.
"""
from functools import lru_cache
import math
import random
from PIL import Image, ImageDraw, ImageFilter

BASE = (1200, 400)
AMPLIACAO = 3


def limites_casas():
    casas = {13: (35, 65, 135, 335), 7: (1065, 65, 1165, 335)}
    for coluna, superior in enumerate((12, 11, 10, 9, 8, 6)):
        x = 169 + coluna * 148
        casas[superior] = (x, 48, x+122, 170)
        casas[coluna] = (x, 222, x+122, 344)
    return casas


@lru_cache(maxsize=1)
def _desenhar_tabuleiro_base():
    tamanho = tuple(v * AMPLIACAO for v in BASE)
    imagem = Image.new('RGBA', tamanho)
    desenho = ImageDraw.Draw(imagem)

    def caixa(valores):
        return tuple(round(v * AMPLIACAO) for v in valores)

    def redondo(limites, raio, cor, borda=None, espessura=1):
        desenho.rounded_rectangle(caixa(limites), raio * AMPLIACAO,
                                  fill=cor, outline=borda, width=espessura*AMPLIACAO)

    sombra = Image.new('RGBA', tamanho)
    ImageDraw.Draw(sombra).rounded_rectangle(caixa((8, 26, 1192, 394)), 58*AMPLIACAO,
                                            fill=(0, 0, 0, 135))
    imagem.alpha_composite(sombra.filter(ImageFilter.GaussianBlur(7*AMPLIACAO)))
    redondo((9, 15, 1191, 386), 51, '#100e10')
    redondo((8, 8, 1192, 378), 51, '#513a2b', '#936b49')
    # Pequenas faixas de tonalidade criam a curvatura da borda, sem ruído forte.
    for recuo, cor in ((2, '#725338'), (4, '#624630'), (6, '#4e3829'), (9, '#3b2b23')):
        redondo((8+recuo, 8+recuo, 1192-recuo, 378-recuo), 51-recuo, cor)
    redondo((23, 23, 1177, 363), 36, '#463329', '#6e5038')
    mascara = Image.new('L', tamanho)
    ImageDraw.Draw(mascara).rounded_rectangle(caixa((24, 24, 1176, 362)), 36*AMPLIACAO, fill=255)
    textura = Image.new('RGBA', tamanho)
    pena = ImageDraw.Draw(textura)
    aleatorio = random.Random(84)
    for linha in range(180):
        y = 25 + linha*1.9
        fase = aleatorio.random()*6.28
        coords = [(x*AMPLIACAO, (y+math.sin(x/100+fase)*1.8)*AMPLIACAO)
                  for x in range(20, 1180, 14)]
        pena.line(coords, fill=(106, 77, 52, aleatorio.randint(20, 55)), width=2)
    textura.putalpha(Image.composite(textura.getchannel('A'), Image.new('L', tamanho), mascara))
    imagem.alpha_composite(textura)
    desenho = ImageDraw.Draw(imagem)
    for posicao, limites in limites_casas().items():
        x1, y1, x2, y2 = limites
        deposito = posicao in (7, 13)
        raio = 48 if deposito else 61
        for deslocamento, cor in ((-4, '#261c19'), (-2, '#8b6648'), (0, '#34261f'),
                                  (2, '#16161a'), (5, '#191a1d'), (8, '#1e2023')):
            ret = (x1+deslocamento, y1+deslocamento, x2-deslocamento, y2-deslocamento)
            if deposito:
                desenho.rounded_rectangle(caixa(ret), max(1, raio-deslocamento)*AMPLIACAO, fill=cor)
            else:
                desenho.ellipse(caixa(ret), fill=cor)
        # Luz suave na metade inferior da cavidade.
        # O desfoque só precisa da região iluminada e sua margem transparente.
        # Evita filtrar o tabuleiro inteiro para cada uma das 14 cavidades.
        bx1, by1, bx2, by2 = caixa((x1+15, y1+(y2-y1)*.6, x2-15, y2-9))
        margem = 3 * 8 * AMPLIACAO
        esquerda, topo = max(0, bx1-margem), max(0, by1-margem)
        direita, fundo = min(tamanho[0], bx2+1+margem), min(tamanho[1], by2+1+margem)
        recorte = Image.new('RGBA', (direita-esquerda, fundo-topo))
        ImageDraw.Draw(recorte).ellipse((bx1-esquerda, by1-topo, bx2-esquerda, by2-topo),
                                        fill=(126, 89, 59, 35))
        imagem.alpha_composite(recorte.filter(ImageFilter.GaussianBlur(8*AMPLIACAO)),
                               dest=(esquerda, topo))
    return imagem


@lru_cache(maxsize=52)
def renderizar_semente(indice_cor, tamanho):
    """Cria uma semente suavizada; os 52 pares de cor/tamanho cabem no cache."""
    if indice_cor not in range(len(CORES_SEMENTES)) or tamanho not in range(6, 31, 2):
        raise ValueError('Cor ou tamanho de semente inválido.')
    cor = CORES_SEMENTES[indice_cor]
    s = 4
    tela = Image.new('RGBA', (tamanho*s, tamanho*s))
    desenho = ImageDraw.Draw(tela)
    r, g, b = cor
    desenho.ellipse((s, 2*s, (tamanho-1)*s, (tamanho-1)*s), fill=(0, 0, 0, 110))
    for nivel in range(tamanho*s//2-3, 0, -1):
        f = nivel/(tamanho*s/2)
        luz = .72 + (1-f)*.55
        cx, cy = tamanho*s*.49, tamanho*s*.46
        desenho.ellipse((cx-nivel, cy-nivel*.84, cx+nivel, cy+nivel*.84),
                        fill=tuple(min(255, round(c*luz)) for c in (r,g,b)))
    reflexo = Image.new('RGBA', tela.size)
    ImageDraw.Draw(reflexo).ellipse((tamanho*s*.22, tamanho*s*.18, tamanho*s*.49, tamanho*s*.31),
                                   fill=(255, 255, 255, 155))
    tela.alpha_composite(reflexo.filter(ImageFilter.GaussianBlur(s*.6)))
    return tela.resize((tamanho, tamanho), Image.Resampling.LANCZOS)


CORES_SEMENTES = ((104, 186, 177), (224, 175, 105), (201, 211, 216), (154, 133, 186))
CORES_ANEIS = {'ativa': '#8bbdba', 'foco': '#e6bf79', 'destaque': '#f3ead7'}


def _validar_largura(largura):
    if largura not in range(360, 1601, 40):
        raise ValueError('A largura deve estar entre 360 e 1600, em passos de 40.')


@lru_cache(maxsize=2)
def renderizar_tabuleiro(largura):
    """Reduz o original com Lanczos; guarda apenas dois tamanhos recentes."""
    _validar_largura(largura)
    return _desenhar_tabuleiro_base().resize(
        (largura, round(largura / 3)), Image.Resampling.LANCZOS)


@lru_cache(maxsize=12)
def renderizar_anel(tipo, largura):
    """Desenha a indicação de casa disponível, foco ou exercício do tutorial."""
    _validar_largura(largura)
    if tipo not in CORES_ANEIS:
        raise ValueError('Tipo de destaque inválido.')
    diametro = round(138 * largura / BASE[0])
    anel = Image.new('RGBA', (diametro * 3, diametro * 3))
    ImageDraw.Draw(anel).ellipse(
        (8, 8, diametro * 3 - 9, diametro * 3 - 9),
        outline=CORES_ANEIS[tipo], width=5 if tipo == 'ativa' else 8)
    return anel.resize((diametro, diametro), Image.Resampling.LANCZOS)
