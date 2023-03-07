class Reminder(object):
    def __init__(self, role, name):
        self.role = role
        self.name = name
    
    def print(self): 
        return f"{self.role}: {self.name}"