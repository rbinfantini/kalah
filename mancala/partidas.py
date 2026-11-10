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
    """
    Representa uma partida persistente com estado, modo e dificuldade.

    Parameters
    ----------
    modo : str, optional
        Tipo de partida: dupla ou contra máquina.
    dificuldade : str, optional
        Nível do computador quando aplicável.
    estado : EstadoPartida, optional
        Estado atual do tabuleiro.
    identificador : str, optional
        Código único da partida.
    jogadas : int, optional
        Número de jogadas já executadas.
    """
    modo: str = 'dupla'
    dificuldade: str = 'Normal'
    estado: EstadoPartida = field(default_factory=estado_inicial)
    identificador: str = field(default_factory=lambda: uuid.uuid4().hex)
    jogadas: int = 0

    def __post_init__(self):
        """
        Valida a partida após a criação do objeto.

        Returns
        -------
        None
            Levanta erro caso o estado não seja consistente.
        """
        validar_estado(self.estado)

    def jogar(self, casa):
        """
        Executa uma jogada da partida e atualiza o estado.

        Parameters
        ----------
        casa : int
            Casa escolhida pelo jogador atual.

        Returns
        -------
        ResultadoJogada
            Resultado completo da jogada, incluindo eventos e novo estado.
        """
        resultado = resolver_jogada(self.estado, casa)
        self.estado = resultado.estado
        self.jogadas += 1
        return resultado


class ArquivoPartidas:
    """
    Gerencia a persistência das partidas em arquivos JSON.

    Parameters
    ----------
    pasta : str or Path
        Diretório usado para armazenar as partidas do usuário.
    """

    def __init__(self, pasta):
        """
        Inicializa a pasta de armazenamento das partidas.

        Parameters
        ----------
        pasta : str or Path
            Caminho do diretório de partidas.
        """
        self.pasta = Path(pasta)

    def salvar(self, partida):
        """
        Salva uma partida em um arquivo JSON atômico.

        Parameters
        ----------
        partida : Partida
            Partida a ser gravada.

        Returns
        -------
        None
            O arquivo é escrito no disco.
        """
        self.pasta.mkdir(parents=True, exist_ok=True)
        dados = asdict(partida)
        dados.update(versao=1, atualizado_em=datetime.now(timezone.utc).isoformat())
        destino = self.pasta / f'{partida.identificador}.json'
        temporario = destino.with_suffix('.tmp')
        temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temporario, destino)

    def carregar(self, caminho):
        """
        Carrega uma partida a partir de um arquivo JSON salvo.

        Parameters
        ----------
        caminho : str or Path
            Arquivo de partida.

        Returns
        -------
        Partida
            Objeto reconstruído a partir do arquivo.
        """
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
        """
        Lista as partidas válidas contidas na pasta de armazenamento.

        Returns
        -------
        tuple
            Tupla com registros ordenados por data e lista de erros de leitura.
        """
        registros = []
        erros = []
        for caminho in self.pasta.glob('*.json'):
            try:
                partida = self.carregar(caminho)
                registros.append((caminho.stat().st_mtime, caminho, partida))
            except (OSError, ValueError, KeyError, TypeError) as erro:
                erros.append(f'{caminho.name}: {erro}')
        return sorted(registros, key=lambda item: item[0], reverse=True), erros
