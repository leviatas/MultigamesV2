from Boardgamebox.State import State as BaseState

class State(BaseState):
	def __init__(self):
		BaseState.__init__(self)
		self.teams = []
		self.team_counter = 0
		self.active_team = None
		self.inactive_team = None
		self.reference = None
		self.team_choosen_grade = -1
		self.opponent_team_choosen_left_right = -1
		
	def increment_team_counter(self):
		if self.team_counter < len(self.teams) - 1:
			self.team_counter += 1			
		else:
			self.team_counter = 0
		self.active_team = self.teams[self.team_counter]
		self.active_team.increment_player_counter()
		self.inactive_team = self.teams[1 if self.team_counter == 0 else 0]
	def swap_team(self):
		if self.team_counter < len(self.teams) - 1:
			self.team_counter += 1			
		else:
			self.team_counter = 0
		self.active_team = self.teams[self.team_counter]
		self.inactive_team = self.teams[1 if self.team_counter == 0 else 0]