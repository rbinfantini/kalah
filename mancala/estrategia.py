"""Minimax, poda alfa-beta, aprofundamento progressivo e cache por busca."""
from dataclasses import dataclass
import random
import time
from .regras import CASAS, DEPOSITOS, casas_disponiveis, resolver_jogada


@dataclass(frozen=True)
class Recomendacao:
    casa: int
    profundidade: int
    posicoes_avaliadas: int


class BuscaInterrompida(Exception):
    pass


def avaliar_posicao(estado, jogador):
    pontos = estado.sementes[DEPOSITOS[jogador]] - estado.sementes[DEPOSITOS[1-jogador]]
    if estado.encerrada:
        return (100000 if pontos > 0 else -100000 if pontos < 0 else 0) + pontos
    reservas = sum(estado.sementes[p] for p in CASAS[jogador]) - sum(
        estado.sementes[p] for p in CASAS[1-jogador])
    return pontos * 100 + reservas


def escolher_jogada(estado, dificuldade='Normal', cancelar=None, *, limite_segundos=None,
                    profundidade_maxima=None):
    opcoes = casas_disponiveis(estado)
    if not opcoes:
        raise ValueError('Não há jogadas disponíveis.')
    if dificuldade not in ('Fácil', 'Normal', 'Difícil'):
        raise ValueError('Dificuldade desconhecida.')
    if dificuldade == 'Fácil':
        return Recomendacao(random.choice(opcoes), 0, 0)
    segundos, profundidade = (0.35, 5) if dificuldade == 'Normal' else (4.0, 28)
    prazo = time.monotonic() + (segundos if limite_segundos is None else limite_segundos)
    profundidade = profundidade if profundidade_maxima is None else profundidade_maxima
    jogador = estado.jogador_atual
    cache = {}
    nos = 0

    def verificar_tempo():
        if (cancelar is not None and cancelar.is_set()) or time.monotonic() >= prazo:
            raise BuscaInterrompida

    def sucessores(posicao):
        resultados = [(p, resolver_jogada(posicao, p, registrar_eventos=False))
                      for p in casas_disponiveis(posicao)]
        # Capturas e turnos extras primeiro aumentam a eficiência da poda.
        resultados.sort(key=lambda item: (item[1].turno_extra, item[1].capturadas), reverse=True)
        return [(p, resultado.estado) for p, resultado in resultados]

    def buscar(posicao, restante, alfa, beta):
        nonlocal nos
        verificar_tempo()
        nos += 1
        if posicao.encerrada or restante == 0:
            return avaliar_posicao(posicao, jogador)
        chave = (posicao, restante)
        alfa_original, beta_original = alfa, beta
        if chave in cache:
            valor, limite = cache[chave]
            if limite == 'exato':
                return valor
            if limite == 'inferior':
                alfa = max(alfa, valor)
            else:
                beta = min(beta, valor)
            if alfa >= beta:
                return valor
        maximizar = posicao.jogador_atual == jogador
        melhor = -float('inf') if maximizar else float('inf')
        for _, seguinte in sucessores(posicao):
            valor = buscar(seguinte, restante - 1, alfa, beta)
            if maximizar:
                melhor = max(melhor, valor)
                alfa = max(alfa, melhor)
            else:
                melhor = min(melhor, valor)
                beta = min(beta, melhor)
            if alfa >= beta:
                break
        limite = 'superior' if melhor <= alfa_original else 'inferior' if melhor >= beta_original else 'exato'
        cache[chave] = melhor, limite
        return melhor

    melhor_casa, concluida = opcoes[0], 0
    for nivel in range(1, profundidade + 1):
        try:
            verificar_tempo()
            alternativas = sucessores(estado)
            alternativas.sort(key=lambda item: item[0] != melhor_casa)
            candidata, pontuacao = melhor_casa, -float('inf')
            for casa, seguinte in alternativas:
                valor = buscar(seguinte, nivel - 1, pontuacao, float('inf'))
                if valor > pontuacao:
                    candidata, pontuacao = casa, valor
            melhor_casa, concluida = candidata, nivel
        except BuscaInterrompida:
            break
    return Recomendacao(melhor_casa, concluida, nos)
