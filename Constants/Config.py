TOKEN = "PUT HERE TOKEN OR IN DB"
ADMIN = [387393551, 441820689, 445782140] #your telegram ID
#Leviatas Ale Cadogan
STATS = "../stats.json"

JUEGOS_DISPONIBLES = {        
        "LostExpedition" : {
                "comandos" : {
                    "LostExpedition" : "Lost Expedition"
                },
                "restriccion" : "admin",                
        },
        "JustOne" : {
                "comandos" : {
                    "JustOne" : "Just One"
                },
		"permitir_ingreso_tardio" : True
        },
        "SistemaD100" : {
                "comandos" : {
                    "SistemaD100" : "SistemaD100"
                },
                "permitir_ingreso_tardio" : True
        },	
	"SayAnything" : {
                "comandos" : {
                    "SayAnything" : "Say Anything"
                },
                "permitir_ingreso_tardio" : True
        },
	"Arcana" : {
                "comandos" : {
                    "Arcana" : "Arcana"
                },
		"permitir_ingreso_tardio" : True
        },
	"Wavelength" : {
                "comandos" : {
                    "Wavelength" : "Wavelength"
                },
		"permitir_ingreso_tardio" : True
		
        },
	"Decrypt" : {
                "comandos" : {
                    "Decrypt" : "Decrypt"
                },
		"permitir_ingreso_tardio" : True
		
        },
        "Resistance" : {
                "comandos" : {
                    "Resistance" : "Resistance"
                },
                "restriccion" : "admin"		
        },
        "Deception" : {
                "comandos" : {
                    "Deception" : "Deception"
                },
                "restriccion" : "admin"		
        },
        "Werewords" : {
                "comandos" : {
                    "Werewords" : "Werewords"
                },	
        },
        "Unanimo" : {
                "comandos" : {
                    "Unanimo" : "Unanimo"
                },
		"permitir_ingreso_tardio" : True
        },
}


HOJAS_AYUDA = {
        "JustOne" : "_Pistas no validas:_\n" + \
		"*Pista con más de 1 palabra.* Ej: El Padrino para Don\n" + \
		"*Pista con ortografia diferente.* Ej: Kamiza para Camisa\n" + \
		"*Palabras escritas en otro idioma.* Ej:Black para Negro\n"  + \
		"*Una palabra de la misma familia* Ej:Principe para Princesa\n"  + \
		"*Una palabra inventada* Ej:Cositadulz para Pastel\n"  + \
		"*Una palabra foneticamente identica.* Ej: Tuvo para Tubo\n" + \
		"Pistas *identicas*\n" + \
		"_Dos palabras identicas._\n" + \
		"*Variantes de una misma familia de palabras* Ej: Princesa y Principe\n" + \
		"*Las variantes de una misma palabra: los plurales, diferencias de genero" + \
		" y faltas de ortografia no cuenta como diferencias reales* Ej: Principe y Principes, " + \
		"Panadero y Panadera, Tobogán y Tovogan son identicas.",	
        "LostExpedition" : "Eventos amarillos son obligatorios\n" + \
		"Eventos rojo son obligatorios pero tenes que elegir 1\n"  + \
		"Eventos Azules son opcionales"        
}

MODULOS_DISPONIBES = {        
        "LostExpedition" : {
                "Solitario" : {
                        "comandos" : {
                            "Solitario" : "Solitario"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 1
                },
                "Cooperativo" : {                        
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 2,
                        "max_jugadores" : 5
                },
                "Competitivo" : {                        
                        "comandos" : {
                            "Competitivo" : "Competitivo"
                        },
                        "min_jugadores" : 2,
                        "max_jugadores" : 2
                } 
        },
        "JustOne" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 15
                },
                "Extreme" : {
                        "comandos" : {
                            "Extreme" : "Extreme"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 15
                } 
        },
	"SayAnything" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 4,
                        "max_jugadores" : 8
                } 
        },
        "SistemaD100" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 99
                } 
        },
	"Wavelength" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 4,
                        "max_jugadores" : 20
                } 
        },
	"Arcana" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 7
                } 
        },
	"Decrypt" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 4,
                        "max_jugadores" : 20
                } 
        },
        "Resistance" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 5,
                        "max_jugadores" : 10
                } 
        },
        "Deception" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 12
                } 
        },
        "Werewords" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 20
                } 
        },
        "Unanimo" : {
                "Cooperativo" : {
                        "comandos" : {
                            "Cooperativo" : "Cooperativo"
                        },
                        "min_jugadores" : 1,
                        "max_jugadores" : 8
                }
                # "Extreme" : {
                #         "comandos" : {
                #             "Extreme" : "Extreme"
                #         },
                #         "min_jugadores" : 1,
                #         "max_jugadores" : 15
                # } 
        },
}
