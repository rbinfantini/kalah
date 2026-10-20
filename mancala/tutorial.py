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
    Etapa('01 · Distribuir', 'Escolha P0. Suas quatro sementes vão para P1, P2, P3 e P4.',
          estado_inicial(), 0, 'Uma semente por posição. Agora seria a vez de B. Os depósitos nunca podem ser escolhidos.'),
    Etapa('02 · Jogar novamente', 'Escolha P2. A última semente vai chegar ao seu depósito P7.',
          estado_inicial(), 2, 'A última semente caiu em P7: A ganha outra escolha. As sementes do depósito ficam guardadas.'),
    Etapa('03 · Capturar', 'Escolha P1. P2 está vazia, e a casa oposta P10 tem quatro sementes.',
          preparar_cenario({0:1, 1:1, 3:1, 4:1, 5:1, 6:1, 8:1, 9:1, 10:4, 11:1, 12:1}, 17), 1,
          'P7 recebeu cinco sementes: a última distribuída e as quatro da casa oposta. Captura não concede turno extra.'),
    Etapa('04 · Dar a volta', 'Escolha P4, com 17 sementes. Observe P7 receber sementes e P13 ser pulado.',
          preparar_cenario({0:1, 1:1, 2:1, 3:1, 4:17, 5:1, 6:1, 8:1, 9:1, 10:1, 11:1, 12:1}, 10), 4,
          'A sequência dá a volta e passa pela origem novamente. Só o depósito adversário é pulado.'),
    Etapa('05 · Encerrar', 'Escolha P5, a única casa de A com sementes. O lado de A ficará vazio.',
          preparar_cenario({5:1, 6:2, 8:3, 9:4, 10:5, 11:6, 12:1}, 20), 5,
          'Fim: A tem 21 e B tem 27. As sobras foram para seus depósitos. O encerramento prevalece sobre o turno extra.'),
)
