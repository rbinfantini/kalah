"""Compara dois EXEs locais; inclui extração do pacote e desenho inicial."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time


def executar(caminho, relatorio):
    comando = [str(caminho)]
    if caminho.suffix in ('.py', '.pyw'):
        comando.insert(0, sys.executable)
    inicio = time.perf_counter()
    subprocess.run(comando + ['--medir-abertura', str(relatorio)], check=True, timeout=60,
                   creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
    resultado = json.loads(relatorio.read_text(encoding='utf-8'))
    return (resultado['pronto_em'] - inicio) * 1000


def comparar(antes, depois, repeticoes):
    amostras = {'antes': [], 'depois': []}
    caminhos = {'antes': antes.resolve(), 'depois': depois.resolve()}
    with tempfile.TemporaryDirectory(prefix='mancala-comparacao-') as pasta:
        # Uma abertura de aquecimento por versão; não confundir com boot frio.
        for nome, caminho in caminhos.items():
            executar(caminho, Path(pasta) / f'aquecimento-{nome}.json')
        for rodada in range(repeticoes):
            ordem = ('antes', 'depois') if rodada % 2 == 0 else ('depois', 'antes')
            for nome in ordem:
                duracao = executar(caminhos[nome], Path(pasta) / f'{nome}-{rodada}.json')
                amostras[nome].append(round(duracao, 2))
    resultado = {'repeticoes': repeticoes, 'resolucao': '1200x800',
                 'metodo': 'processos novos, uma abertura de aquecimento, ordem alternada; até o menu desenhado'}
    for nome, caminho in caminhos.items():
        valores = amostras[nome]
        resultado[nome] = {'arquivo': caminho.name, 'bytes': caminho.stat().st_size,
                           'sha256': hashlib.sha256(caminho.read_bytes()).hexdigest(),
                           'amostras_ms': valores, 'mediana_ms': statistics.median(valores),
                           'minimo_ms': min(valores), 'maximo_ms': max(valores)}
    return resultado


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('antes', type=Path)
    parser.add_argument('depois', type=Path)
    parser.add_argument('--repeticoes', type=int, default=7)
    parser.add_argument('--saida', type=Path, default=Path('build/comparacao-abertura.json'))
    opcoes = parser.parse_args()
    if opcoes.repeticoes < 3:
        parser.error('Use pelo menos três repetições.')
    resultado = comparar(opcoes.antes, opcoes.depois, opcoes.repeticoes)
    opcoes.saida.parent.mkdir(parents=True, exist_ok=True)
    conteudo = json.dumps(resultado, ensure_ascii=False, indent=2)
    opcoes.saida.write_text(conteudo, encoding='utf-8')
    print(conteudo)


if __name__ == '__main__':
    main()
