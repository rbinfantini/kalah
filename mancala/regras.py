"""Kalah com 48 sementes. A numeração pública preserva os depósitos P7/P13."""
from dataclasses import dataclass

TOTAL_SEMENTES = 48
DEPOSITOS = (7, 13)
CASAS = ((0, 1, 2, 3, 4, 5), (6, 8, 9, 10, 11, 12))
PERCURSO = CASAS[0] + (DEPOSITOS[0],) + CASAS[1] + (DEPOSITOS[1],)
PROXIMAS = dict(zip(PERCURSO, PERCURSO[1:] + PERCURSO[:1]))
OPOSTAS = dict(zip(CASAS[0], reversed(CASAS[1])))
OPOSTAS.update({oposta: casa for casa, oposta in tuple(OPOSTAS.items())})


@dataclass(frozen=True)
class EstadoPartida:
    """
    Estado completo de uma partida de Kalah.

    Parameters
    ----------
    sementes : tuple[int, ...]
        Quantidade de sementes em cada posição do tabuleiro.
    jogador_atual : int, optional
        Jogador da vez.
    encerrada : bool, optional
        Indica se o estado já está finalizado.
    """
    sementes: tuple[int, ...]
    jogador_atual: int = 0
    encerrada: bool = False

    @property
    def placar(self):
        """
        Retorna o placar atual dos dois jogadores.

        Returns
        -------
        tuple[int, int]
            Sementes acumuladas nos depósitos dos jogadores.
        """
        return tuple(self.sementes[p] for p in DEPOSITOS)

    @property
    def vencedor(self):
        """
        Informa o vencedor final da partida, quando ela já está encerrada.

        Returns
        -------
        int or None
            0, 1 ou None em caso de empate ou partida em andamento.
        """
        a, b = self.placar
        return None if not self.encerrada or a == b else int(b > a)


@dataclass(frozen=True)
class EventoJogada:
    """
    Registro de um passo da animação da jogada.

    Parameters
    ----------
    tipo : str
        Tipo do evento gerado pela distribuição.
    sementes : tuple[int, ...]
        Estado do tabuleiro após o passo.
    na_mao : int
        Quantidade restante de sementes em mãos.
    posicao : int or None
        Posição diretamente afetada pelo evento.
    """
    tipo: str
    sementes: tuple[int, ...]
    na_mao: int
    posicao: int | None


@dataclass(frozen=True)
class ResultadoJogada:
    """
    Resultado completo de uma jogada validada pelo motor de regras.

    Parameters
    ----------
    estado : EstadoPartida
        Estado do tabuleiro após a jogada.
    eventos : tuple[EventoJogada, ...]
        Sequência de eventos usados pela animação.
    capturadas : int
        Número total de sementes capturadas na jogada.
    turno_extra : bool
        Indica se o jogador pode repetir a jogada.
    """
    estado: EstadoPartida
    eventos: tuple[EventoJogada, ...]
    capturadas: int
    turno_extra: bool


def estado_inicial():
    """
    Cria a configuração inicial padrão de uma partida de Kalah.

    Returns
    -------
    EstadoPartida
        Tabuleiro com quatro sementes em cada casa e depósitos vazios.
    """
    return EstadoPartida(tuple(0 if p in DEPOSITOS else 4 for p in range(14)))


def validar_estado(estado):
    """
    Verifica se um estado do jogo respeita as regras de integridade.

    Parameters
    ----------
    estado : EstadoPartida
        Estado a ser validado.

    Raises
    ------
    ValueError
        Quando o estado não representa uma partida válida.
    """
    if len(estado.sementes) != 14:
        raise ValueError('São necessárias 14 posições.')
    if any(type(n) is not int or not 0 <= n <= TOTAL_SEMENTES for n in estado.sementes):
        raise ValueError('Cada posição deve conter entre 0 e 48 sementes.')
    if sum(estado.sementes) != TOTAL_SEMENTES:
        raise ValueError('A partida deve conservar as 48 sementes.')
    if type(estado.jogador_atual) is not int or estado.jogador_atual not in (0, 1):
        raise ValueError('Jogador inválido.')
    if type(estado.encerrada) is not bool:
        raise ValueError('Situação da partida inválida.')
    vazios = [all(estado.sementes[p] == 0 for p in lado) for lado in CASAS]
    if (estado.encerrada and not all(vazios)) or (not estado.encerrada and any(vazios)):
        raise ValueError('O encerramento não corresponde às casas do tabuleiro.')


def proxima_posicao(posicao, jogador):
    """
    Calcula a próxima casa no percurso do jogador.

    Parameters
    ----------
    posicao : int
        Casa atual.
    jogador : int
        Jogador cujo percurso está sendo percorrido.

    Returns
    -------
    int
        Próxima posição válida no caminho do jogador.
    """
    seguinte = PROXIMAS[posicao]
    if seguinte == DEPOSITOS[1 - jogador]:
        seguinte = PROXIMAS[seguinte]
    return seguinte


def casas_disponiveis(estado):
    """
    Lista as casas do jogador atual que ainda possuem sementes.

    Parameters
    ----------
    estado : EstadoPartida
        Estado atual da partida.

    Returns
    -------
    tuple[int, ...]
        Casas jogáveis no momento.
    """
    if estado.encerrada:
        return ()
    return tuple(p for p in CASAS[estado.jogador_atual] if estado.sementes[p])


def resolver_jogada(estado, casa, *, registrar_eventos=True):
    """
    Executa uma jogada inteira e retorna o resultado com eventos opcionais.

    Parameters
    ----------
    estado : EstadoPartida
        Estado antes da jogada.
    casa : int
        Casa escolhida pelo jogador atual.
    registrar_eventos : bool, optional
        Controla se a animação deve registrar a sequência de eventos.

    Returns
    -------
    ResultadoJogada
        Novo estado, eventos e metadados da jogada.
    """
    if type(casa) is not int or casa not in casas_disponiveis(estado):
        raise ValueError('Escolha uma casa sua com sementes. Depósitos não podem ser jogados.')
    sementes = list(estado.sementes)
    jogador = estado.jogador_atual
    deposito = DEPOSITOS[jogador]
    eventos = []
    na_mao = sementes[casa]
    sementes[casa] = 0

    def registrar(tipo, posicao=None):
        if registrar_eventos:
            eventos.append(EventoJogada(tipo, tuple(sementes), na_mao, posicao))

    registrar('retirada', casa)
    posicao = casa
    while na_mao:
        posicao = proxima_posicao(posicao, jogador)
        sementes[posicao] += 1
        na_mao -= 1
        registrar('distribuicao', posicao)

    capturadas = 0
    if posicao in CASAS[jogador] and sementes[posicao] == 1:
        oposta = OPOSTAS[posicao]
        if sementes[oposta]:
            capturadas = sementes[oposta] + 1
            sementes[deposito] += capturadas
            sementes[posicao] = sementes[oposta] = 0
            registrar('captura', deposito)

    encerrada = any(all(sementes[p] == 0 for p in lado) for lado in CASAS)
    if encerrada:
        for dono, lado in enumerate(CASAS):
            sementes[DEPOSITOS[dono]] += sum(sementes[p] for p in lado)
            for p in lado:
                sementes[p] = 0
        registrar('recolha')
    turno_extra = posicao == deposito and not encerrada
    proximo_jogador = jogador if turno_extra or encerrada else 1 - jogador
    depois = EstadoPartida(tuple(sementes), proximo_jogador, encerrada)
    return ResultadoJogada(depois, tuple(eventos), capturadas, turno_extra)
