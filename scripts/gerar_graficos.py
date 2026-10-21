"""Gera os recursos originais com supersampling. Pillow é usado só nesta etapa."""
from pathlib import Path
import math
import random
from PIL import Image, ImageDraw, ImageFilter

DESTINO = Path(__file__).resolve().parents[1] / 'mancala' / 'recursos'
BASE = (1200, 400)
AMPLIACAO = 3


def geometria():
    casas = {13: (35, 65, 135, 335), 7: (1065, 65, 1165, 335)}
    for coluna, superior in enumerate((12, 11, 10, 9, 8, 6)):
        x = 169 + coluna * 148
        casas[superior] = (x, 48, x+122, 170)
        casas[coluna] = (x, 222, x+122, 344)
    return casas


def tabuleiro():
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
    for posicao, limites in geometria().items():
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
        brilho = Image.new('RGBA', tamanho)
        ImageDraw.Draw(brilho).ellipse(caixa((x1+15, y1+(y2-y1)*.6, x2-15, y2-9)),
                                      fill=(126, 89, 59, 35))
        imagem.alpha_composite(brilho.filter(ImageFilter.GaussianBlur(8*AMPLIACAO)))
    return imagem


def semente(tamanho, cor):
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


def gerar():
    DESTINO.mkdir(parents=True, exist_ok=True)
    original = tabuleiro()
    # Recursos em tamanho nativo: o aplicativo nunca estica bitmaps nem círculos.
    for largura in range(360, 1601, 40):
        altura = round(largura/3)
        original.resize((largura, altura), Image.Resampling.LANCZOS).save(
            DESTINO / f'tabuleiro-{largura}.png', optimize=True)
        diametro = round(138*largura/1200)
        for nome, cor in [('ativa', '#8bbdba'), ('foco', '#e6bf79'), ('destaque', '#f3ead7')]:
            anel = Image.new('RGBA', (diametro*3, diametro*3))
            desenho = ImageDraw.Draw(anel)
            desenho.ellipse((8,8,diametro*3-9,diametro*3-9), outline=cor, width=5 if nome=='ativa' else 8)
            anel.resize((diametro, diametro), Image.Resampling.LANCZOS).save(
                DESTINO/f'{nome}-{largura}.png', optimize=True)
    for tamanho in range(6, 31, 2):
        for indice, cor in enumerate(((104,186,177), (224,175,105), (201,211,216), (154,133,186))):
            semente(tamanho, cor).save(DESTINO/f'semente-{indice}-{tamanho}.png', optimize=True)
    print(f'{len(list(DESTINO.glob("*.png")))} recursos gráficos gerados.')


if __name__ == '__main__':
    gerar()
