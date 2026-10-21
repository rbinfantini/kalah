"""Exercícios usam o mesmo motor das partidas e conservam 48 sementes."""
from dataclasses import dataclass
from .regras import EstadoPartida, estado_inicial


@dataclass(frozen=True)
class Etapa:
    titulo: str
    instrucao: str
    estado: EstadoPartida
    casa: int
    conclusao: str


def preparar_cenario(casas, deposito_a):
    sementes = [0] * 14
    for posicao, quantidade in casas.items():
        sementes[posicao] = quantidade
    sementes[7] = deposito_a
    sementes[13] = 48 - sum(sementes)
    return EstadoPartida(tuple(sementes))


ETAPAS = (
    Etapa('01 · Distribuir', 'Clique na casa iluminada. Suas quatro sementes serão distribuídas pelas casas seguintes.',
          estado_inicial(), 0, 'Uma semente em cada casa. Agora seria a vez do adversário. Os depósitos guardam as sementes até o fim.'),
    Etapa('02 · Jogar novamente', 'Escolha a casa iluminada. A última semente chegará ao seu depósito, à direita.',
          estado_inicial(), 2, 'A última semente caiu no seu depósito: você ganhou outra jogada!'),
    Etapa('03 · Capturar', 'Escolha a casa iluminada. A seguinte está vazia, mas a casa à sua frente tem quatro sementes.',
          preparar_cenario({0:1, 1:1, 3:1, 4:1, 5:1, 6:1, 8:1, 9:1, 10:4, 11:1, 12:1}, 17), 1,
          'Você capturou cinco sementes: a sua e as quatro da casa oposta. Todas foram para o seu depósito.'),
    Etapa('04 · Dar a volta', 'Escolha a casa iluminada, com 17 sementes. A distribuição vai dar a volta no tabuleiro.',
          preparar_cenario({0:1, 1:1, 2:1, 3:1, 4:17, 5:1, 6:1, 8:1, 9:1, 10:1, 11:1, 12:1}, 10), 4,
          'A sequência dá a volta e passa pela origem novamente. Só o depósito adversário é pulado.'),
    Etapa('05 · Encerrar', 'Escolha a única casa iluminada. Sua fileira ficará vazia e a partida terminará.',
          preparar_cenario({5:1, 6:2, 8:3, 9:4, 10:5, 11:6, 12:1}, 20), 5,
          'Fim de jogo: 21 a 27. As sementes restantes foram para o depósito de cada jogador. Vence quem guardou mais.'),
)
