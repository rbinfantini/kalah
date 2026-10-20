import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from mancala.caminhos import pasta_dados


class TestCaminhos(unittest.TestCase):
    def test_codigo_preserva_partidas_na_pasta_do_projeto(self):
        with patch.object(sys, 'frozen', False, create=True):
            self.assertEqual(pasta_dados(), Path(__file__).resolve().parents[1])

    def test_executavel_grava_fora_das_bibliotecas(self):
        with patch.object(sys, 'frozen', True, create=True), patch.dict(os.environ, {'LOCALAPPDATA': 'dados-usuario'}):
            self.assertEqual(pasta_dados(), Path('dados-usuario') / 'MancalaSoJoga')
