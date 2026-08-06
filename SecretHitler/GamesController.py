def init():
    global games
    games = {}

# Estado en memoria de sesiones /guess en curso: (cid, uid) -> {"fascists": [...], "hitler": uid|None, "num_fascists": int}
guess_progress = {}