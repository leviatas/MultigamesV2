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

    def _ficha_en_carrera(self, game, rid):
        """Ficha del corredor más los poderes que ganó en la carrera actual
        (los que robó el Mutante, o el prestado del Cambiante, Heredero, etc.)."""
        texto = ficha(rid)
        st = getattr(getattr(game, "board", None), "state", None)
        if st is None or st.fase_actual != "Carrera":
            return texto
        for c in st.corredores:
            if c.rid == rid and c.uid == self.uid:
                extra = [p for p in c.poderes if p != c.rid]
                if extra:
                    titulo = "🧬 Mutó y también tiene" if c.rid == "mutante" else "➕ Ahora tiene"
                    texto += "\n   {}:\n".format(titulo) + "\n".join("   " + ficha(p) for p in extra)
                break
        return texto

    def get_private_info(self, game):
        texto = "--- 🏆 *Gran Premio Arcano* — {} ---\n".format(self.name)
        texto += "Puntos: *{}*\n\n".format(self.puntos)
        if self.elegidos:
            texto += "*Corriendo en esta carrera:*\n" + "\n".join(
                self._ficha_en_carrera(game, r) for r in self.elegidos) + "\n\n"
        libres = [r for r in self.corredores if r not in self.usados and r not in self.elegidos]
        if libres:
            texto += "*Disponibles para próximas carreras:*\n" + "\n".join(ficha(r) for r in libres) + "\n\n"
        if self.usados:
            texto += "*Ya corrieron:* " + ", ".join(etiqueta(r) for r in self.usados)
        return texto
