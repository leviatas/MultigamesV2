from Boardgamebox.State import State as BaseState


class Bicho(object):
    def __init__(self, bid):
        self.bid = bid
        self.pos = 0
        self.mareado = 0  # movimientos que le quedan mareado
        self.dormido = False
        self.lugar = None  # 1..4 cuando termina


class State(BaseState):
    def __init__(self):
        BaseState.__init__(self)
        # Apuestas -> Aportes -> Carrera -> (Apuestas ...) -> Finalizado
        self.fase_actual = "Apuestas"
        self.carrera = 1
        self.bichos = []

        # --- Apuestas ---
        self.boletos = {}          # clave de boleto -> lista de pagos que quedan
        self.especial = None       # id de la apuesta especial de esta carrera
        self.orden_apuestas = []   # uids en orden (serpiente)
        self.apuesta_idx = 0
        self.boleto_pendiente = None  # boleto elegido esperando "normal/fuerte"
        self.apuesta_msg_id = None
        self.primer_apostador_uid = None

        # --- Mazo de la carrera ---
        self.mazo_base = []        # cartas públicas de la carrera
        self.aportes = {}          # str(uid) -> carta aportada en secreto
        self.mazo = []             # pila para robar
        self.quemadas = []
        self.descarte = []
        self.reveladas = 0
        self.mezclas = 0

        # --- Transmisión ---
        self.podio = []            # bids en orden de llegada
        self.stats = {}
        self.ticker = []           # últimos sucesos para el relato
        self.live_msg_id = None
        self.ganadores_uids = []
