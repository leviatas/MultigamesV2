playerSets = {    
    4: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    5: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    6: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    7: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Complice", "Asesino"),
            ("Testigo", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    8: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Complice", "Asesino"),
            ("Testigo", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    9: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Complice", "Asesino"),
            ("Testigo", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    10: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Complice", "Asesino"),
            ("Testigo", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    # Oraculo es Beholder
    11: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Complice", "Asesino"),
            ("Testigo", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    },
    12: {
        "afiliacion": [
            ("Forense", "Policia"),
            ("Asesino", "Asesino"),
            ("Complice", "Asesino"),
            ("Testigo", "Policia"),
            ("Investigador", "Policia"),            
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia"),
            ("Investigador", "Policia")
        ]
    }
}

clues = ["tinta", "horquilla", "revista", "engranaje", "mouse", "juego de construcción", 
        "números", "vegetales", "fax", "plancha", "ceniza de tabaco", "hoja", "folleto",
        "bombilla","ficha de apuestas", "circuito electrónico", "manzana", "fiambrera",
        "dentadura", "saco", "juguete", "carta de amor", "sombrero", "rosa", "peluca",
        "periódico", "planta", "ficha de mahjong", "pastel", "pelaje de perro", "cigarro",
        "carta confidencial"]

means = ["virus", "cirugia", "ácido sulfúrico", "ahogamiento", "aguja envenenada",
        "agua sucia", "gancho", "puñetazo", "puñal", "tijeras", "cable", "toalla",
        "patada", "cinturón", "motosierra", "drogas en polvo", "llave inglesa",
        "piedra", "cuchilla de afeitar", "químicos", "droga líquida", "maceta",
        "muleta", "serpiente venenosa", "explosivos", "pildora", "consola de videojuegos",
        "escorpión Venenoso", "hacha", "látigo", "corriente elécrtrica", "queroseno",
        "empujón", "ameba", "taladro", "humo"]


FORENSIC_CARDS = {
    "causa de la muerte" : {
        1 : {
            "Asfixia" : False,
        },
        2 : {
            "Herida severa" : False,
        },
        3 : {
            "Perdida de sangre" : False,
        },
        4 : {
            "Enfermedad" : False,
        },
        5 : {
            "Envenenamiento" : False,
        },
        6 : {
            "Accidente" : False
        }
    },
    "localization" : 
    {
        "Localización 1" : {
            1 : {
                "Salón" : False,
            },
            2 : {
                "Habitación" : False,
            },
            3 : {
                "Despensa" : False,
            },
            4 : {
                "Cuarto de baño" : False,
            },
            5 : {
                "Cocina" : False,
            },
            6 : {
                "Balcón" : False
            }
        },   
        "Localización 2" : 
        {
            1 : {
                "Casa de vacaciones" : False,
            },
            2 : {
                "Parque" : False,
            },
            3 : {
                "Supermercado" : False,
            },
            4 : {
                "Colegio" : False,
            },
            5 : {
                "Bosque" : False,
            },
            6 : {
                "Banco" : False
            }
        },    
        "Localización 3" : {
            1 : {
                "Bar" : False,
            },
            2 : {
                "Librería" : False,
            },
            3 : {
                "Restaurante" : False,
            },
            4 : {
                "Hotel" : False,
            },
            5 : {
                "Hospital" : False,
            },
            6 : {
                "Sitio de construcción" : False
            }
        },    
        "Localización 4" : {
            1 : {
                "Patio de recreo" : False,
            },
            2 : {
                "Aula" : False,
            },
            3 : {
                "Dormitorio" : False,
            },
            4 : {
                "Cafeteria" : False,
            },
            5 : {
                "Ascensor" : False,
            },
            6 : {
                "Inodoro" : False
            }
        }
    },
    "scene" : 
    {
        "Motivo del Crimen" : {
            1 : {
                "odio" : False,
            },
            2 : {
                "Energía" : False,
            },
            3 : {
                "Dinero" : False,
            },
            4 : {
                "Amor" : False,
            },
            5 : {
                "Celos" : False,
            },
            6 : {
                "Justicia" : False
            }
        },
        "Clima" : {
            1 : {
                "Soleado" : False,
            },
            2 : {
                "Tormentoso" : False,
            },
            3 : {
                "Seco" : False,
            },
            4 : {
                "humedo" : False,
            },
            5 : {
                "Frio" : False,
            },
            6 : {
                "Caliente" : False
            }
        },
        "Insinuación sobre el cuerpo" : {
            1 : {
                "Cabeza" : False,
            },
            2 : {
                "Pecho" : False,
            },
            3 : {
                "Mano" : False,
            },
            4 : {
                "Pierna" : False,
            },
            5 : {
                "Parcial" : False,
            },
            6 : {
                "Por todas partes" : False
            }
        },
        "Impresión general" : {
            1 : {
                "Común" : False,
            },
            2 : {
                "Creativo" : False,
            },
            3 : {
                "Sospechoso" : False,
            },
            4 : {
                "Cruel" : False,
            },
            5 : {
                "Horrible" : False,
            },
            6 : {
                "Suspenso" : False
            }            
        },
        "Hora de la muerte" : {
            1 : {
                "Amanecer" : False,
            },
            2 : {
                "Mañana" : False,
            },
            3 : {
                "Mediodía" : False,
            },
            4 : {
                "Tarde" : False,
            },
            5 : {
                "Anochecer" : False,
            },
            6 : {
                "Medianoche" : False
            }
        }, 
        "Duración del crimen" : {
            1 : {
                "Instantáneo" : False,
            },
            2 : {
                "Breve" : False,
            },
            3 : {
                "Gradual" : False,
            },
            4 : {
                "Prolongado" : False,
            },
            5 : {
                "Pocos días" : False,
            },
            6 : {
                "Incierto" : False
            }
        },
        "Escena del crimen" : {
            1 : {
                "Huella dactilar" : False,
            },
            2 : {
                "Huella pisadas" : False,
            },
            3 : {
                "Moretón" : False,
            },
            4 : {
                "Manchas de sangre" : False,
            },
            5 : {
                "Fluído corporal" : False,
            },
            6 : {
                "Cicatriz" : False
            }
        },
        "Observado por testigos" : {
                1 : {
                    "Sonido repentino" : False,
                },
                2 : {
                    "Sonido prolongado" : False,
                },
                3 : {
                    "Algo olía" : False,
                },
                4 : {
                    "Visual" : False,
                },
                5 : {
                    "Acción" : False,
                },
                6 : {
                    "Nada" : False
                }
        },
        "Condición del cuerpo" : {
            1 : {
                "Aún tibio" : False,
            },
            2 : {
                "Rígido" : False,
            },
            3 : {
                "Deteriorado" : False,
            },
            4 : {
                "Incompleto" : False,
            },
            5 : {
                "Intacto" : False,
            },
            6 : {
                "Retorcido" : False
            }
        },
        "Identidad de la victima" : {
            1 : {
                "Niño" : False,
            },
            2 : {
                "Adolecente" : False,
            },
            3 : {
                "Mediana edad" : False,
            },
            4 : {
                "Avanzada edad" : False,
            },
            5 : {
                "Hombre" : False,
            },
            6 : {
                "Mujer" : False
            }
        },
    }
}

modules = {
    "Contemplador": {
        "roles": {
            "Policia": "Contemplador"
        }
    },
    "Secuaz": {
        "roles": {
            "Policia": "Secuaz"
        }
    },
}

