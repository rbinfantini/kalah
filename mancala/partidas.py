"""Partidas em JSON. Gravação atômica evita arquivos parcialmente escritos."""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
import json
import os
import uuid
from .regras import EstadoPartida, estado_inicial, resolver_jogada, validar_estado


@dataclass
class Partida:
    modo: str = 'dupla'
    dificuldade: str = 'Normal'
    estado: EstadoPartida = field(default_factory=estado_inicial)
    identificador: str = field(default_factory=lambda: uuid.uuid4().hex)
    jogadas: int = 0

    def __post_init__(self):
        validar_estado(self.estado)

    def jogar(self, casa):
        resultado = resolver_jogada(self.estado, casa)
        self.estado = resultado.estado
        self.jogadas += 1
        return resultado


class ArquivoPartidas:
    def __init__(self, pasta):
        self.pasta = Path(pasta)

    def salvar(self, partida):
        self.pasta.mkdir(parents=True, exist_ok=True)
        dados = asdict(partida)
        dados.update(versao=1, atualizado_em=datetime.now(timezone.utc).isoformat())
        destino = self.pasta / f'{partida.identificador}.json'
        temporario = destino.with_suffix('.tmp')
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporario, destino)

    def carregar(self, caminho):
        dados = json.loads(Path(caminho).read_text(encoding='utf-8'))
        if dados['versao'] != 1:
            raise ValueError('Versão de arquivo não reconhecida.')
        bruto = dados['estado']
        estado = EstadoPartida(tuple(bruto['sementes']), bruto['jogador_atual'], bruto['encerrada'])
        validar_estado(estado)
        if dados['modo'] not in ('dupla', 'maquina') or dados['dificuldade'] not in ('Fácil', 'Normal', 'Difícil'):
            raise ValueError('Configuração inválida.')
        identidade = dados['identificador']
        if not isinstance(identidade, str) or len(identidade) != 32 or any(c not in '0123456789abcdef' for c in identidade):
            raise ValueError('Identificador inválido.')
        if type(dados['jogadas']) is not int or dados['jogadas'] < 0:
            raise ValueError('Número de jogadas inválido.')
        return Partida(dados['modo'], dados['dificuldade'], estado, identidade, dados['jogadas'])

    def listar(self):
        registros = []
        erros = []
        for caminho in self.pasta.glob('*.json'):
            try:
                partida = self.carregar(caminho)
                registros.append((caminho.stat().st_mtime, caminho, partida))
            except (OSError, ValueError, KeyError, TypeError) as erro:
                erros.append(f'{caminho.name}: {erro}')
        return sorted(registros, key=lambda item: item[0], reverse=True), erros
