from Boardgamebox.Player import Player as BasePlayer
from GranPremioArcano.Constants.Corredores import ficha, etiqueta


class Player(BasePlayer):
    def __init__(self, name, uid):
        BasePlayer.__init__(self, name, uid)
        self.puntos = 0
        self.corredores = []  # ids de corredores del equipo
        self.usados = []      # ids que ya corrieron
        self.elegidos = []    # ids elegidos para la carrera actual

    def disponibles(self):
        return [r for r in self.corredores if r not in self.usados and r not in self.elegidos]

    def get_private_info(self, game):
        texto = "--- 🏆 *Gran Premio Arcano* — {} ---\n".format(self.name)
        texto += "Puntos: *{}*\n\n".format(self.puntos)
        if self.elegidos:
            texto += "*Corriendo en esta carrera:*\n" + "\n".join(ficha(r) for r in self.elegidos) + "\n\n"
        libres = [r for r in self.corredores if r not in self.usados and r not in self.elegidos]
        if libres:
            texto += "*Disponibles para próximas carreras:*\n" + "\n".join(ficha(r) for r in libres) + "\n\n"
        if self.usados:
            texto += "*Ya corrieron:* " + ", ".join(etiqueta(r) for r in self.usados)
        return texto
