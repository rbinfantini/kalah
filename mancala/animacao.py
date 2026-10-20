"""Reprodução visual independente das regras e do relógio da interface."""
class AnimadorJogada:
    def __init__(self):
        self.eventos = ()
        self.indice = 0
        self.espera = 0.0

    @property
    def ativo(self):
        return self.indice < len(self.eventos)

    def iniciar(self, eventos):
        self.eventos = eventos
        self.indice = 0
        self.espera = 0.0

    def avancar(self, segundos):
        self.espera -= segundos
        if not self.ativo or self.espera > 0:
            return None
        evento = self.eventos[self.indice]
        self.indice += 1
        self.espera = 0.42 if evento.tipo in ('captura', 'recolha') else 0.16
        return evento
