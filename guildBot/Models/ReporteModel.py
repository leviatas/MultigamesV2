class ReporteModel(object):
    def __init__(self, report_date, chat_wars_name, castle, guild, attack, \
                defense, player_level, experience, gold, stock, lost_hp):
        self.report_date = report_date
        self.chat_wars_name = chat_wars_name
        self.castle = castle
        self.guild = guild
        self.attack = attack
        self.defense = defense
        self.player_level = player_level
        self.experience = experience
        self.gold = gold
        self.stock = stock
        self.lost_hp = lost_hp
    def get_formated_report(self):
        string_date = self.report_date.strftime("%H:%M %d.%m")
        return f"{string_date} ⚔{self.attack} 🛡{self.defense}: 🔥Exp: {self.experience} 💰{self.gold} 📦 {self.stock}"