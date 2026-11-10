"""Reprodução visual independente das regras e do relógio da interface."""


class AnimadorJogada:
    """
    Controla a reprodução sequencial de eventos de uma jogada.

    Parameters
    ----------
    None
        O estado inicial é configurado em __init__.

    Attributes
    ----------
    eventos : tuple
        Sequência de eventos a ser reproduzida.
    indice : int
        Posição atual do evento em execução.
    espera : float
        Tempo restante até o próximo passo da animação.
    """

    def __init__(self):
        """
        Inicializa o animador em estado ocioso.

        Returns
        -------
        None
            Cria a estrutura interna de controle da animação.
        """
        self.eventos = ()
        self.indice = 0
        self.espera = 0.0

    @property
    def ativo(self):
        """
        Indica se ainda há eventos pendentes para reprodução.

        Returns
        -------
        bool
            True quando existe um próximo evento a processar.
        """
        return self.indice < len(self.eventos)

    def iniciar(self, eventos):
        """
        Configura a sequência de eventos a ser animada.

        Parameters
        ----------
        eventos : tuple
            Lista ou tupla de eventos da jogada.

        Returns
        -------
        None
            Reinicia o estado do animador para a nova reprodução.
        """
        self.eventos = eventos
        self.indice = 0
        self.espera = 0.0

    def avancar(self, segundos):
        """
        Avança a animação pelo tempo informado e retorna o próximo evento quando pronto.

        Parameters
        ----------
        segundos : float
            Tempo decorrido desde a última atualização.

        Returns
        -------
        object or None
            O próximo evento processado ou None quando ainda não chegou o momento.

        Notes
        -----
        Recebe tempo decorrido, já ajustado pela velocidade da interface.
        Retorna no máximo um evento por chamada; o primeiro pode sair de
        imediato. Após o fim retorna None. Não altera a partida nem salva dados.
        """
        self.espera -= segundos
        if not self.ativo or self.espera > 0:
            return None
        evento = self.eventos[self.indice]
        self.indice += 1
        self.espera = 0.42 if evento.tipo in ('captura', 'recolha') else 0.16
        return evento
