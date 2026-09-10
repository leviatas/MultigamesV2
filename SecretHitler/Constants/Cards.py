playerSets = {
    # only for testing purposes
    3: {
        "roles": [
            "Liberal",
            "Fascista",
            "Hitler"
        ],
        "track": [
            None,
            None,
            "policy",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    # only for testing purposes
    4: {
        "roles": [
            "Liberal",
            "Liberal",
            "Fascista",
            "Hitler"
        ],
        "track": [
            None,
            None,
            "policy",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    5: {
        "roles": [
            "Liberal",
            "Liberal",
            "Liberal",
            "Fascista",
            "Hitler"
        ],
        "track": [
            None,
            None,
            "policy",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    6: {
        "roles": [
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Fascista",
            "Hitler"
        ],
        "track": [
            None,
            None,
            "policy",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    7: {
        "roles": [
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Fascista",
            "Fascista",
            "Hitler"
        ],
        "track": [
            None,
            "inspect",
            "choose",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    8: {
        "roles": [
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Fascista",
            "Fascista",
            "Hitler"
        ],
        "track": [
            None,
            "inspect",
            "choose",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    9: {
        "roles": [
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Fascista",
            "Fascista",
            "Fascista",
            "Hitler"
        ],
        "track": [
            "inspect",
            "inspect",
            "choose",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
    10: {
        "roles": [
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Liberal",
            "Fascista",
            "Fascista",
            "Fascista",
            "Hitler"
        ],
        "track": [
            "inspect",
            "inspect",
            "choose",
            "kill",
            "kill",
            "win"
        ],
        "policies": [
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "liberal",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista",
            "fascista"
        ]
    },
}

policies = [
        "liberal",
        "liberal",
        "liberal",
        "liberal",
        "liberal",
        "liberal",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista",
        "fascista"
    ]

##
# Expansion Socialista (Secret Hitler: Socialist Expansion, de Matej Haverlik y Daniel Teplan).
# Agrega un tercer partido con su propia pista, su propio mazo y sus propios poderes.
# Se usa solo en partidas creadas con "/newgame socialista"; el modo clasico sigue
# leyendo playerSets de arriba y no cambia en nada.
##

# Poderes de la pista socialista, en orden de promulgacion. Se ejecutan apenas se
# promulga la politica (incluso por anarquia, a diferencia de los poderes presidenciales).
# Hay tres pistas distintas segun la cantidad de jugadores, tal como vienen impresas
# en las laminas de la expansion.

# 6 a 8 jugadores ("Short"): alcanza con 5 politicas socialistas para ganar.
PISTA_SOCIALISTA_CORTA = [
    "escucha",
    "reclutamiento",
    "plan_quinquenal",
    "congreso",
    "win"
]

# 9 y 10 jugadores ("Congress"): la unica que tiene Confesion ademas de Congreso.
PISTA_SOCIALISTA_CONGRESO = [
    "escucha",
    "reclutamiento",
    "plan_quinquenal",
    "congreso",
    "confesion",
    "win"
]

# 11 o mas jugadores ("Double Recruitment"): dos reclutamientos, sin Escucha ni Congreso,
# y la primera casilla no da ningun poder.
PISTA_SOCIALISTA_DOBLE_RECLUTAMIENTO = [
    None,
    "reclutamiento",
    "plan_quinquenal",
    "reclutamiento",
    "confesion",
    "win"
]

# Cantidad de politicas socialistas promulgadas a partir de la cual se activa la Censura:
# no es un poder de una casilla puntual, funciona como la Zona Hitler (una vez activada
# queda activa el resto de la partida) y elimina la figura del Presidente de la Camara.
CENSURA_DESDE = 3

# Pista fascista de la expansion (la lamina titulada "Socialist"): es una sola para todas
# las cantidades de jugadores, y no coincide con ninguna de las clasicas. El Veto se
# habilita con la quinta politica fascista, igual que siempre.
PISTA_FASCISTA_SOCIALISTA = [
    None,
    "inspect",
    "policy",
    "kill",
    "kill",
    "win"
]


def _mazo_socialista(liberales, fascistas, socialistas):
    # El mazo se baraja al crear el Board, asi que el orden de esta lista no importa.
    return ["liberal"] * liberales + ["fascista"] * fascistas + ["socialista"] * socialistas


def _roles_socialistas(liberales, fascistas, socialistas):
    return ["Liberal"] * liberales + ["Fascista"] * fascistas + ["Hitler"] + ["Socialista"] * socialistas


def _set_socialista(liberales, fascistas, socialistas, pista_socialista, mazo_liberales, mazo_fascistas, pista_liberal):
    return {
        "roles": _roles_socialistas(liberales, fascistas, socialistas),
        "track": list(PISTA_FASCISTA_SOCIALISTA),
        "socialist_track": list(pista_socialista),
        "liberal_track": pista_liberal,
        "policies": _mazo_socialista(mazo_liberales, mazo_fascistas, 8),
    }


# Reparto de roles segun el reglamento de la expansion (6 a 13 jugadores). El mazo base es
# 5 liberales / 10 fascistas / 8 socialistas; en partidas de 8 jugadores se saca una politica
# fascista y se agrega una liberal (6/9/8), que es la unica que ademas usa la pista liberal
# larga (6 actas en vez de 5).
socialistSets = {
    6: _set_socialista(3, 1, 1, PISTA_SOCIALISTA_CORTA, 5, 10, 5),
    7: _set_socialista(4, 1, 1, PISTA_SOCIALISTA_CORTA, 5, 10, 5),
    8: _set_socialista(4, 2, 1, PISTA_SOCIALISTA_CORTA, 6, 9, 6),
    9: _set_socialista(4, 2, 2, PISTA_SOCIALISTA_CONGRESO, 5, 10, 5),
    10: _set_socialista(5, 2, 2, PISTA_SOCIALISTA_CONGRESO, 5, 10, 5),
    11: _set_socialista(5, 3, 2, PISTA_SOCIALISTA_DOBLE_RECLUTAMIENTO, 5, 10, 5),
    12: _set_socialista(6, 3, 2, PISTA_SOCIALISTA_DOBLE_RECLUTAMIENTO, 5, 10, 5),
    13: _set_socialista(6, 3, 3, PISTA_SOCIALISTA_DOBLE_RECLUTAMIENTO, 5, 10, 5),
}

opciones_choose_posible_role = {
    "Liberal" : {
        "comandos" : {
            1 : "Liberal"
        }
    },
    "Fascista" : {        
        "comandos" : {
            1 : "Fascista"
        }
    },
    "Hitler" : {        
        "comandos" : {
            1 : "Hitler"
        }
    },
    "Liberal_Fascista" : {
        "comandos" : {
            1 : "Liberal o Fascista"
        }
    },
    "Liberal_Hitler" : {
        "comandos" : {
            1 : "Liberal o Hitler"
        }
    },
    "Fascista_Hitler" : {        
        "comandos" : {
            1 : "Fascista o Hitler"
        }
    }
}
