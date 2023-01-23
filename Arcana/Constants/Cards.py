PLAYERFATETOKENS = [
	{
		"Texto" : "1",
		"TimeSymbols" : "1",
		"Enable" : True
	},
	{
		"Texto" : "2",
		"TimeSymbols" : "1",
		"Enable" : True
	},
	{
		"Texto" : "3",
		"TimeSymbols" : "1",
		"Enable" : True
	},
	{
		"Texto" : "4",
		"TimeSymbols" : "2",
		"Enable" : True
	},
	{
		"Texto" : "5",
		"TimeSymbols" : "2",
		"Enable" : True
	},
	{
		"Texto" : "6",
		"TimeSymbols" : "2",
		"Enable" : True
	},	
	{
		"Texto" : "7",
		"TimeSymbols" : "3",
		"Enable" : True
	}
]
	

FATETOKENS = [
	{
		"Texto" : "1",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "1",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "1",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "2",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "2",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "2",
		"TimeSymbols" : "1"
	},	
	{
		"Texto" : "3",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "3",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "3",
		"TimeSymbols" : "1"
	},
	{
		"Texto" : "4",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "4",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "4",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "5",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "5",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "5",
		"TimeSymbols" : "2"
	},	
	{
		"Texto" : "6",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "6",
		"TimeSymbols" : "2"
	},
	{
		"Texto" : "6",
		"TimeSymbols" : "2"
	},	
	{
		"Texto" : "7",
		"TimeSymbols" : "3"
	},
	{
		"Texto" : "7",
		"TimeSymbols" : "3"
	},
	{
		"Texto" : "7",
		"TimeSymbols" : "3"
	}	
]

LASHORAS = {	
	"Título": "Las horas",
	"Texto": "Si no podés jugar tu destino en ningún otro lado, hacelo aquí. Después, movelo una carta a la derecha.",
	"Lunas": "99",
	"Título reverso": "",
	"Texto reverso": "",
	"Legal": lambda kept, played, my_tokens, all_tokens: True,
	"tokens" : []
}

ARCANACARDS = [ 
 {
   "Título": "1-4-7",
   "Texto": "Si uno de tus destinos es 1, 4 o 7, y el otro no, juega el 1, 4 o 7 aquí.",
   "Lunas": "3",
   "Título reverso": "¿Dentro de 2?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿La diferencia entre tus destinos era de 2 o menos?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played in [1,4,7] and kept not in [1,4,7],
   "tokens" : []
 },
 {
   "Título": "Dentro de 2",
   "Texto": "Si la diferencia entre tus destinos es 1 o 2, jugá uno de ellos aquí",
   "Lunas": "2",
   "Título reverso": "¿Dentro de 2?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿La diferencia entre tus destinos era de 2 o menos?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: abs(kept-played) in [1,2],
   "tokens" : []
 },
 {
   "Título": "Levantamiento",
   "Texto": "Si uno de tus destinos es mayor que el destino más alto jugado aquí, jugá el otro destino aquí.",
   "Lunas": "4",
   "Título reverso": "+1",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para tratar el destino no jugado como si fuera 1 más alto durante este turno.",
   "Legal": lambda kept, played, my_tokens, all_tokens: len(my_tokens) == 0 or kept > max(my_tokens),
   "tokens" : []
 },
 {
   "Título": "Solo",
   "Texto": "Si ningún destino visible es exactamente 1 más o 1 menos que cualquiera de tus destinos, jugá uno de ellos aquí.",
   "Lunas": "2",
   "Título reverso": "+1",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para tratar el destino no jugado como si fuera 1 más alto durante este turno.",
   "Legal": lambda kept, played, my_tokens, all_tokens: (kept-1) not in all_tokens and (kept+1) not in all_tokens and (played-1) not in all_tokens and (played+1) not in all_tokens,
   "tokens" : []
 },
 {
   "Título": "Igual",
   "Texto": "Si tus dos destinos son iguales, jugá uno de ellos aquí.",
   "Lunas": "1",
   "Título reverso": "Repetir",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para hacer una predicción extra este turno.",
   "Legal": lambda kept, played, my_tokens, all_tokens: played == kept,
   "tokens" : []
 },
 {
   "Título": "Todos x4",
   "Texto": "Si la suma de tus destinos más todos los destinos visibles es un múltiplo de 4, jugá uno de tus destinos aquí.",
   "Lunas": "3",
   "Título reverso": "Reubicar",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para mover un destino visible a una nueva carta.",
   "Legal": lambda kept, played, my_tokens, all_tokens: (played + kept + sum(all_tokens)) % 4 == 0,
   "tokens" : []
 },
 {
   "Título": "Altas probabilidades",
   "Texto": "Si tus destinos son diferentes y ambos impares, jugá el más alto aquí. Si solo uno es impar, jugá el más bajo aquí.",
   "Lunas": "3",
   "Título reverso": "+1",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para tratar el destino no jugado como si fuera 1 más alto durante este turno.",
   "Legal": lambda kept, played, my_tokens, all_tokens: (played % 2 + kept % 2 > 0) and (((kept+played) % 2 == 0 and played > kept) or ((kept+played) % 2 != 0 and kept > played)),
   "tokens" : []
 },
 {
   "Título": "±1",
   "Texto": "Si uno de tus destinos es exactamente 1 más o 1 menos que el otro, jugá uno de ellos aquí.",
   "Lunas": "1",
   "Título reverso": "Repetir",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para hacer una predicción extra este turno.",
   "Legal": lambda kept, played, my_tokens, all_tokens: abs(played - kept) == 1,
   "tokens" : []
 },
 {
   "Título": "Menor",
   "Texto": "Si uno de tus destinos es menor que el otro, jugá el menor aquí",
   "Lunas": "3",
   "Título reverso": "¿Mayor que?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para elegir un número X y preguntar \"¿Tu destino es mayor que X?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played < kept,
   "tokens" : []
 },
 {
   "Título": "Libre",
   "Texto": "Colocá uno de tus destinos aquí. No avances la condena cuando me desvanezca.",
   "Lunas": "1",
   "Título reverso": "1-4-7",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 1, 4 o 7?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: True,
   "tokens" : []
 },
 {
   "Título": "≥11",
   "Texto": "Si la suma de tus destinos es 11 o más, jugá uno de ellos aquí",
   "Lunas": "4",
   "Título reverso": "Descartar menor",
   "Texto reverso": "Después de jugar su destino, el jugador activo puede descartar esta carta para descartar un destino visible que sea menor que el destino restante.",
   "Legal": lambda kept, played, my_tokens, all_tokens: played + kept >= 11,
   "tokens" : []
 },
 {
   "Título": "Coincidencia",
   "Texto": "Si uno de tus destinos coincide con uno visible, jugá tu otro destino aquí.",
   "Lunas": "2",
   "Título reverso": "Ciclar",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para reemplazar una carta arcana (sin destinos) por la carta superior del mazo.",
   "Legal": lambda kept, played, my_tokens, all_tokens: kept in all_tokens,
   "tokens" : []
 },
 {
   "Título": "x3",
   "Texto": "Si la suma de tus destinos es un múltiplo de 3, jugá uno de ellos aquí.",
   "Lunas": "2",
   "Título reverso": "Descartar menor",
   "Texto reverso": "Después de jugar su destino, el jugador activo puede descartar esta carta para descartar un destino visible que sea menor que el destino restante.",
   "Legal": lambda kept, played, my_tokens, all_tokens: (played + kept) % 3 == 0,
   "tokens" : []
 },
 {
   "Título": "5-6-7",
   "Texto": "Si uno de tus destinos es 5, 6 o 7, y el otro no, juega el 5, 6 o 7 aquí.",
   "Lunas": "3",
   "Título reverso": "5-6-7",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 5, 6 o 7?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played in [5,6,7] and kept not in [5,6,7],
   "tokens" : []
 },
 {
   "Título": "7 a 9",
   "Texto": "Si la suma de tus destinos es 7, 8 o 9, jugá uno de ellos aquí.",
   "Lunas": "3",
   "Título reverso": "¿Viejo?",
   "Texto reverso": "Después de jugar su destino, el jugador activo puede descartar esta carta para decir si tenía ese destino desde el turno anterior.",
   "Legal": lambda kept, played, my_tokens, all_tokens: (played + kept) in [7,8,9],
   "tokens" : []
 },
 {
   "Título": "Adivinar",
   "Texto": "Colocá uno de tus destinos aquí. Si lo hacés, tus compañeros pueden hacer una predicción extra este turno.",
   "Lunas": "2",
   "Título reverso": "¿Viejo?",
   "Texto reverso": "Después de jugar su destino, el jugador activo puede descartar esta carta para decir si tenía ese destino desde el turno anterior.",
   "Legal": lambda kept, played, my_tokens, all_tokens: True,
   "tokens" : []
 },
 {
   "Título": "Diferencia",
   "Texto": "Si la diferencia entre tus destinos es igual a un destino visible, jugá el mayor aquí",
   "Lunas": "1",
   "Título reverso": "¿Igual?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para elegir un destino visible y preguntar \"¿Tu destino es igual?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played > kept and (played - kept) in all_tokens,
   "tokens" : []
 },
 {
   "Título": "Factor",
   "Texto": "Si uno de tus destinos es el doble o el triple del otro, jugá uno de ellos aquí.",
   "Lunas": "3",
   "Título reverso": "5-6-7",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 5, 6 o 7?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played == 2*kept or played == 3*kept or kept == 2*played or kept == 3*played,
   "tokens" : []
 },
 {
   "Título": "1-2-3",
   "Texto": "Si uno de tus destinos es 1, 2 o 3, y el otro no, juega el 1, 2 o 3 aquí.",
   "Lunas": "2",
   "Título reverso": "1-2-3",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 1, 2 o 3?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played in [1,2,3] and kept not in [1,2,3],
   "tokens" : []
 },
 {
   "Título": "Sacar",
   "Texto": "Colocá uno de tus destinos aquí, sacá otro destino y continuá tu turno. No podés jugar aquí nuevamente.",
   "Lunas": "4",
   "Título reverso": "Reubicar",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para mover un destino visible a una nueva carta.",
   "Legal": lambda kept, played, my_tokens, all_tokens: True,
   "tokens" : []
 },
 {
   "Título": "Decir",
   "Texto": "Colocá uno de tus destinos aquí. Si lo hacés, decí si tu destino restante es mayor que el que jugaste.",
   "Lunas": "2",
   "Título reverso": "1-4-7",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 1, 4 o 7?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: True,
   "tokens" : []
 },
 {
   "Título": "Impar",
   "Texto": "Si la suma de tus destinos es impar, jugá uno de ellos aquí.",
   "Lunas": "3",
   "Título reverso": "1-2-3",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 1, 2 o 3?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: (played + kept) % 2 != 0,
   "tokens" : []
 },
 {
   "Título": "Mayor",
   "Texto": "Si uno de tus destinos es mayor que el otro, jugá el mayor aquí",
   "Lunas": "3",
   "Título reverso": "¿Mayor que?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para elegir un número X y preguntar \"¿Tu destino es mayor que X?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played > kept,
   "tokens" : []
 },
 {
   "Título": "±2",
   "Texto": "Si uno de tus destinos es exactamente 2 más o 2 menos que el otro, jugá uno de ellos aquí.",
   "Lunas": "1",
   "Título reverso": "Repetir",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para hacer una predicción extra este turno.",
   "Legal": lambda kept, played, my_tokens, all_tokens: abs(played - kept) == 2,
   "tokens" : []
 },
 {
   "Título": "≤5",
   "Texto": "Si la suma de tus destinos es 5 o menos, jugá uno de ellos aquí",
   "Lunas": "3",
   "Título reverso": "¿Mayor que?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para elegir un número X y preguntar \"¿Tu destino es mayor que X?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played + kept <= 5,
   "tokens" : []
 },
 {
   "Título": "Único",
   "Texto": "Si tus dos destinos son diferentes entre sí y de todos los otros destinos visibles, jugá uno de ellos aquí",
   "Lunas": "2",
   "Título reverso": "Ciclar",
   "Texto reverso": "Antes de jugar el destino, el jugador activo puede descartar esta carta para reemplazar una carta arcana (sin destinos) por la carta superior del mazo.",
   "Legal": lambda kept, played, my_tokens, all_tokens: played != kept and kept not in all_tokens and played not in all_tokens,
   "tokens" : []
 },
 {
   "Título": "Entre",
   "Texto": "Si exactamente un destino visible se ubica entre tus destinos, jugá uno de ellos aquí.",
   "Lunas": "2",
   "Título reverso": "¿Igual?",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para elegir un destino visible y preguntar \"¿Tu destino es igual?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: len(list(filter(lambda x: x in range(min(kept, played)+1, max(kept, played)), all_tokens))) == 1,
   "tokens" : []
 },
 {
   "Título": "Separados 4",
   "Texto": "Si la diferencia entre tus destinos es 4 o más, jugá uno de ellos aquí.",
   "Lunas": "4",
   "Título reverso": "Descartar menor",
   "Texto reverso": "Después de jugar su destino, el jugador activo puede descartar esta carta para descartar un destino visible que sea menor que el destino restante.",
   "Legal": lambda kept, played, my_tokens, all_tokens: abs(played - kept) >= 4,
   "tokens" : []
 },
 {
   "Título": "Par",
   "Texto": "Si la suma de tus destinos es par, jugá uno de ellos aquí.",
   "Lunas": "3",
   "Título reverso": "3-4-5",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 3, 4 o 5?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: (played + kept) % 2 == 0,
   "tokens" : []
 },
 {
   "Título": "3-4-5",
   "Texto": "Si uno de tus destinos es 3, 4 o 5, y el otro no, juega el 3, 4 o 5 aquí.",
   "Lunas": "3",
   "Título reverso": "3-4-5",
   "Texto reverso": "Antes de hacer una predicción, el grupo puede descartar esta carta para preguntar \"¿Tu destino es 3, 4 o 5?\".",
   "Legal": lambda kept, played, my_tokens, all_tokens: played in [3,4,5] and kept not in [3,4,5],
   "tokens" : []
 },
]
