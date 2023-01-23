from Utils import user_call

class UserModel(object):
    def __init__(self, uid, name, guild = "", castle= "", attack = "", defense = "", last_report = None):
        self.uid = uid
        self.name = name
        self.guild = guild
        self.castle = castle
        self.attack = attack
        self.defense = defense
    def get_call(self):
        descripcion = f"{self.guild.replace('[', '').replace(']', '')} {self.name}"
        return f"{user_call(descripcion, self.uid)}"