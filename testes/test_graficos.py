"""Regressão visual sem manter os antigos PNGs no repositório."""
import hashlib
import unittest
from mancala.graficos import renderizar_tabuleiro, renderizar_anel, renderizar_semente


class TestGraficos(unittest.TestCase):
    def test_preserva_pixels_da_interface_aprovada(self):
        # SHA256 dos pixels RGBA dos PNGs de v0.2.0, antes da migração.
        referencias = [
            (renderizar_tabuleiro, (360,), '043c8a6fe10ab5473f49e132fea441f6f1be48fdb3d6daeba30522500718ce14'),
            (renderizar_tabuleiro, (1000,), '03926a9a2fde50606ede718c7f6f46b5ee8ab279fb94dd1d8f0f493a4e6cc3d5'),
            (renderizar_tabuleiro, (1600,), 'd21084a0b91a71ea8da27b9bf01479099a795fe1af25204f70aa04c700958b09'),
            (renderizar_anel, ('ativa', 1000), '8965f4ae6e1b0f5f0b2f961714ba101a7e5c574bd7bf2c551710d08f50b150e2'),
            (renderizar_anel, ('foco', 1000), '7b66027a62a31cc53ac18043233ed0af9354be547bc8631011d098ecad60d80d'),
            (renderizar_anel, ('destaque', 1000), 'e87006663e9fa8a54e9f89da5f987b3a049eb6120cabed11debb5a8e818aa3e4'),
            (renderizar_semente, (0, 6), '722bd18ddca4f74541f5c65b8d42f34a59f7829bd3607a5b2fd999cb6a813383'),
            (renderizar_semente, (1, 14), '327b09ce563469dc8727313121794d3319419a1e3ec32c3f4c2905610903685f'),
            (renderizar_semente, (3, 30), '46fc8ee722723110705b75dac7b295b5e0fe58ba9bdbf913d8396a5e5bcdc0a6'),
        ]
        for renderizar, argumentos, esperado in referencias:
            with self.subTest(funcao=renderizar.__name__, argumentos=argumentos):
                imagem = renderizar(*argumentos)
                self.assertEqual(imagem.mode, 'RGBA')
                self.assertEqual(hashlib.sha256(imagem.tobytes()).hexdigest(), esperado)

    def test_cache_limitado_ao_redimensionar(self):
        for largura in range(360, 1601, 40):
            renderizar_tabuleiro(largura)
            for tipo in ('ativa', 'foco', 'destaque'):
                renderizar_anel(tipo, largura)
        self.assertLessEqual(renderizar_tabuleiro.cache_info().currsize, 2)
        self.assertLessEqual(renderizar_anel.cache_info().currsize, 12)
        self.assertIs(renderizar_tabuleiro(1600), renderizar_tabuleiro(1600))

    def test_rejeita_dimensoes_fora_do_limite(self):
        for largura in (0, -1, 359, 1601, 10000):
            with self.subTest(largura=largura), self.assertRaises(ValueError):
                renderizar_tabuleiro(largura)
        with self.assertRaises(ValueError):
            renderizar_semente(4, 14)
        with self.assertRaises(ValueError):
            renderizar_semente(0, 10000)


if __name__ == '__main__':
    unittest.main()
