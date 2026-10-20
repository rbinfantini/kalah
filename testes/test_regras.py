import json
from pathlib import Path
import random
import tempfile
import unittest
from mancala.regras import (CASAS, DEPOSITOS, PERCURSO, EstadoPartida, casas_disponiveis,
                            estado_inicial, proxima_posicao, resolver_jogada, validar_estado)
from mancala.estrategia import avaliar_posicao, escolher_jogada
from mancala.partidas import ArquivoPartidas, Partida
from mancala.tutorial import ETAPAS


class TestRegras(unittest.TestCase):
    def test_inicio_e_percurso(self):
        estado = estado_inicial()
        validar_estado(estado)
        self.assertEqual(estado.placar, (0, 0))
        self.assertEqual(sum(estado.sementes), 48)
        self.assertEqual(set(PERCURSO), set(range(14)))
        for jogador in (0, 1):
            visitadas = []
            posicao = CASAS[jogador][0]
            for _ in range(13):
                posicao = proxima_posicao(posicao, jogador)
                visitadas.append(posicao)
            self.assertEqual(len(set(visitadas)), 13)
            self.assertNotIn(DEPOSITOS[1-jogador], visitadas)
            self.assertIn(DEPOSITOS[jogador], visitadas)

    def test_depositos_nao_podem_ser_jogados(self):
        for deposito in DEPOSITOS:
            with self.assertRaises(ValueError):
                resolver_jogada(estado_inicial(), deposito)

    def test_jogada_extra(self):
        resultado = resolver_jogada(estado_inicial(), 2)
        self.assertTrue(resultado.turno_extra)
        self.assertEqual(resultado.estado.jogador_atual, 0)
        self.assertEqual(resultado.estado.sementes[7], 1)

    def test_tutorial_captura_e_encerramento(self):
        for etapa in ETAPAS:
            validar_estado(etapa.estado)
            validar_estado(resolver_jogada(etapa.estado, etapa.casa).estado)
        self.assertEqual(resolver_jogada(ETAPAS[2].estado, ETAPAS[2].casa).capturadas, 5)
        final = resolver_jogada(ETAPAS[4].estado, ETAPAS[4].casa)
        self.assertEqual(final.estado.placar, (21, 27))
        self.assertTrue(final.estado.encerrada)
        self.assertFalse(final.turno_extra)

    def test_posicoes_comportam_48_sementes(self):
        for p in range(14):
            sementes = [0]*14
            sementes[p] = 48
            estado = EstadoPartida(tuple(sementes), encerrada=p in DEPOSITOS)
            self.assertEqual(estado.sementes[p], 48)
            if p in DEPOSITOS:
                validar_estado(estado)

    def test_cem_partidas_preservam_sementes_e_depositos(self):
        aleatorio = random.Random(42)
        for _ in range(100):
            estado = estado_inicial()
            for jogada in range(1000):
                if estado.encerrada:
                    break
                anterior = estado
                resultado = resolver_jogada(estado, aleatorio.choice(casas_disponiveis(estado)))
                estado = resultado.estado
                validar_estado(estado)
                fotografias = [evento.sementes for evento in resultado.eventos]
                for evento in resultado.eventos:
                    self.assertEqual(sum(evento.sementes) + evento.na_mao, 48)
                for antes, depois in zip([anterior.sementes] + fotografias, fotografias):
                    for deposito in DEPOSITOS:
                        self.assertGreaterEqual(depois[deposito], antes[deposito])
            self.assertTrue(estado.encerrada)

    def test_busca_equivale_a_minimax_sem_poda(self):
        def referencia(estado, nivel, jogador):
            if estado.encerrada or nivel == 0:
                return avaliar_posicao(estado, jogador)
            valores = [referencia(resolver_jogada(estado, casa, registrar_eventos=False).estado,
                                  nivel-1, jogador) for casa in casas_disponiveis(estado)]
            return (max if estado.jogador_atual == jogador else min)(valores)
        for estado in (estado_inicial(), ETAPAS[2].estado, ETAPAS[4].estado):
            recomendacao = escolher_jogada(estado, 'Difícil', limite_segundos=10, profundidade_maxima=4)
            self.assertEqual(recomendacao.profundidade, 4)
            valor = referencia(resolver_jogada(estado, recomendacao.casa).estado, 3, estado.jogador_atual)
            self.assertEqual(valor, referencia(estado, 4, estado.jogador_atual))

    def test_busca_sem_tempo(self):
        for nivel in ('Fácil', 'Normal', 'Difícil'):
            sugestao = escolher_jogada(estado_inicial(), nivel, limite_segundos=0)
            self.assertIn(sugestao.casa, casas_disponiveis(estado_inicial()))

    def test_persistencia_e_arquivos_invalidos(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = ArquivoPartidas(pasta)
            partida = Partida('maquina', 'Difícil')
            partida.jogar(2)
            arquivo.salvar(partida)
            caminho = Path(pasta) / f'{partida.identificador}.json'
            self.assertEqual(arquivo.carregar(caminho), partida)
            (Path(pasta) / 'corrompido.json').write_text('inválido', encoding='utf-8')
            registros, erros = arquivo.listar()
            self.assertEqual((len(registros), len(erros)), (1, 1))
            dados = json.loads(caminho.read_text(encoding='utf-8'))
            dados['identificador'] = '../escape'
            caminho.write_text(json.dumps(dados), encoding='utf-8')
            with self.assertRaises(ValueError):
                arquivo.carregar(caminho)


if __name__ == '__main__':
    unittest.main()
