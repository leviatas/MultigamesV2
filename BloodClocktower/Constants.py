playerSets = {
    # only for testing purposes
    
    5: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Minions",
            "Demons"
        ],
    },
    6: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Minions",
            "Demons"
        ],
    },
    7: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Minions",
            "Demons"
        ],
    },
    8: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Minions",
            "Demons"
        ],
    },
    9: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Outsiders",
            "Minions",
            "Demons"
        ],
    },
    10: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Minions",
            "Minions",
            "Demons"
        ],
    },
    11: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Minions",
            "Minions",
            "Demons"
        ],
    },
    12: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Outsiders",
            "Minions",
            "Minions",
            "Demons"
        ],
    },
    13: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Minions",
            "Minions",
            "Minions",
            "Demons"
        ],
    },
    14: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Minions",
            "Minions",
            "Minions",
            "Demons"
        ],
    },
    15: {
        "roles": [
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Townfolk",
            "Outsiders",
            "Outsiders",
            "Minions",
            "Minions",
            "Minions",
            "Demons"
        ],
    },
}


roles = [
  {
    "id": "washerwoman",
    "name": "Washerwoman",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 33,
    "firstNightReminder": "Show the character token of a Townsfolk in play. Point to two players, one of which is that character.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Townsfolk",
        "Wrong"],
    "setup": False,
    "ability": "You start knowing that 1 of 2 players is a particular Townsfolk."
  },
  {
    "id": "librarian",
    "name": "Librarian",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 34,
    "firstNightReminder": "Show the character token of an Outsider in play. Point to two players, one of which is that character.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Outsider",
        "Wrong"],
    "setup": False,
    "ability": "You start knowing that 1 of 2 players is a particular Outsider. (Or that zero are in play.)"
  },
  {
    "id": "investigator",
    "name": "Investigator",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 35,
    "firstNightReminder": "Show the character token of a Minion in play. Point to two players, one of which is that character.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Minion",
        "Wrong"],
    "setup": False,
    "ability": "You start knowing that 1 of 2 players is a particular Minion."
  },
  {
    "id": "chef",
    "name": "Chef",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 36,
    "firstNightReminder": "Show the finger signal (0, 1, 2, \u2026) for the number of pairs of neighbouring evil players.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "You start knowing how many pairs of evil players there are."
  },
  {
    "id": "empath",
    "name": "Empath",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 37,
    "firstNightReminder": "Show the finger signal (0, 1, 2) for the number of evil alive neighbours of the Empath.",
    "otherNight": 53,
    "otherNightReminder": "Show the finger signal (0, 1, 2) for the number of evil neighbours.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, you learn how many of your 2 alive neighbours are evil."
  },
  {
    "id": "fortuneteller",
    "name": "Fortune Teller",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 38,
    "firstNightReminder": "The Fortune Teller points to two players. Give the head signal (nod yes, shake no) for whether one of those players is the Demon. ",
    "otherNight": 54,
    "otherNightReminder": "The Fortune Teller points to two players. Show the head signal (nod 'yes', shake 'no') for whether one of those players is the Demon.",
    "reminders": ["Red herring"],
    "setup": False,
    "ability": "Each night, choose 2 players: you learn if either is a Demon. There is a good player that registers as a Demon to you."
  },
  {
    "id": "undertaker",
    "name": "Undertaker",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 55,
    "otherNightReminder": "If a player was executed today: Show that player\u2019s character token.",
    "reminders": ["Executed"],
    "setup": False,
    "ability": "Each night*, you learn which character died by execution today."
  },
  {
    "id": "monk",
    "name": "Monk",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 12,
    "otherNightReminder": "The previously protected player is no longer protected. The Monk points to a player not themself. Mark that player 'Protected'.",
    "reminders": ["Protected"],
    "setup": False,
    "ability": "Each night*, choose a player (not yourself): they are safe from the Demon tonight."
  },
  {
    "id": "ravenkeeper",
    "name": "Ravenkeeper",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 52,
    "otherNightReminder": "If the Ravenkeeper died tonight: The Ravenkeeper points to a player. Show that player\u2019s character token.",
    "reminders": [],
    "setup": False,
    "ability": "If you die at night, you are woken to choose a player: you learn their character."
  },
  {
    "id": "virgin",
    "name": "Virgin",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "The 1st time you are nominated, if the nominator is a Townsfolk, they are executed immediately."
  },
  {
    "id": "slayer",
    "name": "Slayer",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, during the day, publicly choose a player: if they are the Demon, they die."
  },
  {
    "id": "soldier",
    "name": "Soldier",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "You are safe from the Demon."
  },
  {
    "id": "mayor",
    "name": "Mayor",
    "edition": "tb",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If only 3 players live & no execution occurs, your team wins. If you die at night, another player might die instead."
  },
  {
    "id": "butler",
    "name": "Butler",
    "edition": "tb",
    "team": "outsider",
    "firstNight": 39,
    "firstNightReminder": "The Butler points to a player. Mark that player as 'Master'.",
    "otherNight": 67,
    "otherNightReminder": "The Butler points to a player. Mark that player as 'Master'.",
    "reminders": ["Master"],
    "setup": False,
    "ability": "Each night, choose a player (not yourself): tomorrow, you may only vote if they are voting too."
  },
  {
    "id": "drunk",
    "name": "Drunk",
    "edition": "tb",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "remindersGlobal": ["Drunk"],
    "setup": True,
    "ability": "You do not know you are the Drunk. You think you are a Townsfolk character, but you are not."
  },
  {
    "id": "recluse",
    "name": "Recluse",
    "edition": "tb",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "You might register as evil & as a Minion or Demon, even if dead."
  },
  {
    "id": "saint",
    "name": "Saint",
    "edition": "tb",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If you die by execution, your team loses."
  },
  {
    "id": "poisoner",
    "name": "Poisoner",
    "edition": "tb",
    "team": "minion",
    "firstNight": 17,
    "firstNightReminder": "The Poisoner points to a player. That player is poisoned.",
    "otherNight": 7,
    "otherNightReminder": "The previously poisoned player is no longer poisoned. The Poisoner points to a player. That player is poisoned.",
    "reminders": ["Poisoned"],
    "setup": False,
    "ability": "Each night, choose a player: they are poisoned tonight and tomorrow day."
  },
  {
    "id": "spy",
    "name": "Spy",
    "edition": "tb",
    "team": "minion",
    "firstNight": 49,
    "firstNightReminder": "Show the Grimoire to the Spy for as long as they need.",
    "otherNight": 68,
    "otherNightReminder": "Show the Grimoire to the Spy for as long as they need.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, you see the Grimoire. You might register as good & as a Townsfolk or Outsider, even if dead."
  },
  {
    "id": "scarletwoman",
    "name": "Scarlet Woman",
    "edition": "tb",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 19,
    "otherNightReminder": "If the Scarlet Woman became the Demon today: Show the 'You are' card, then the demon token.",
    "reminders": ["Demon"],
    "setup": False,
    "ability": "If there are 5 or more players alive & the Demon dies, you become the Demon. (Travellers don\u2019t count)"
  },
  {
    "id": "baron",
    "name": "Baron",
    "edition": "tb",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": True,
    "ability": "There are extra Outsiders in play. [+2 Outsiders]"
  },
  {
    "id": "imp",
    "name": "Imp",
    "edition": "tb",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 24,
    "otherNightReminder": "The Imp points to a player. That player dies. If the Imp chose themselves: Replace the character of 1 alive minion with a spare Imp token. Show the 'You are' card, then the Imp token.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each night*, choose a player: they die. If you kill yourself this way, a Minion becomes the Imp."
  },
  {
    "id": "bureaucrat",
    "name": "Bureaucrat",
    "edition": "tb",
    "team": "traveler",
    "firstNight": 1,
    "firstNightReminder": "The Bureaucrat points to a player. Put the Bureaucrat's '3 votes' reminder by the chosen player's character token.",
    "otherNight": 1,
    "otherNightReminder": "The Bureaucrat points to a player. Put the Bureaucrat's '3 votes' reminder by the chosen player's character token.",
    "reminders": ["3 votes"],
    "setup": False,
    "ability": "Each night, choose a player (not yourself): their vote counts as 3 votes tomorrow."
  },
  {
    "id": "thief",
    "name": "Thief",
    "edition": "tb",
    "team": "traveler",
    "firstNight": 1,
    "firstNightReminder": "The Thief points to a player. Put the Thief's 'Negative vote' reminder by the chosen player's character token.",
    "otherNight": 1,
    "otherNightReminder": "The Thief points to a player. Put the Thief's 'Negative vote' reminder by the chosen player's character token.",
    "reminders": ["Negative vote"],
    "setup": False,
    "ability": "Each night, choose a player (not yourself): their vote counts negatively tomorrow."
  },
  {
    "id": "gunslinger",
    "name": "Gunslinger",
    "edition": "tb",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Each day, after the 1st vote has been tallied, you may choose a player that voted: they die."
  },
  {
    "id": "scapegoat",
    "name": "Scapegoat",
    "edition": "tb",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If a player of your alignment is executed, you might be executed instead."
  },
  {
    "id": "beggar",
    "name": "Beggar",
    "edition": "tb",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "You must use a vote token to vote. Dead players may choose to give you theirs. If so, you learn their alignment. You are sober & healthy."
  },
  {
    "id": "grandmother",
    "name": "Grandmother",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 40,
    "firstNightReminder": "Show the marked character token. Point to the marked player.",
    "otherNight": 51,
    "otherNightReminder": "If the Grandmother\u2019s grandchild was killed by the Demon tonight: The Grandmother dies.",
    "reminders": ["Grandchild"],
    "setup": False,
    "ability": "You start knowing a good player & their character. If the Demon kills them, you die too."
  },
  {
    "id": "sailor",
    "name": "Sailor",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 11,
    "firstNightReminder": "The Sailor points to a living player. Either the Sailor, or the chosen player, is drunk.",
    "otherNight": 4,
    "otherNightReminder": "The previously drunk player is no longer drunk. The Sailor points to a living player. Either the Sailor, or the chosen player, is drunk.",
    "reminders": ["Drunk"],
    "setup": False,
    "ability": "Each night, choose an alive player: either you or they are drunk until dusk. You can't die."
  },
  {
    "id": "chambermaid",
    "name": "Chambermaid",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 51,
    "firstNightReminder": "The Chambermaid points to two players. Show the number signal (0, 1, 2, \u2026) for how many of those players wake tonight for their ability.",
    "otherNight": 70,
    "otherNightReminder": "The Chambermaid points to two players. Show the number signal (0, 1, 2, \u2026) for how many of those players wake tonight for their ability.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, choose 2 alive players (not yourself): you learn how many woke tonight due to their ability."
  },
  {
    "id": "exorcist",
    "name": "Exorcist",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 21,
    "otherNightReminder": "The Exorcist points to a player, different from the previous night. If that player is the Demon: Wake the Demon. Show the Exorcist token. Point to the Exorcist. The Demon does not act tonight.",
    "reminders": ["Chosen"],
    "setup": False,
    "ability": "Each night*, choose a player (different to last night): the Demon, if chosen, learns who you are then doesn't wake tonight."
  },
  {
    "id": "innkeeper",
    "name": "Innkeeper",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 9,
    "otherNightReminder": "The previously protected and drunk players lose those markers. The Innkeeper points to two players. Those players are protected. One is drunk.",
    "reminders": ["Protected",
        "Drunk"],
    "setup": False,
    "ability": "Each night*, choose 2 players: they can't die tonight, but 1 is drunk until dusk."
  },
  {
    "id": "gambler",
    "name": "Gambler",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 10,
    "otherNightReminder": "The Gambler points to a player, and a character on their sheet. If incorrect, the Gambler dies.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each night*, choose a player & guess their character: if you guess wrong, you die."
  },
  {
    "id": "gossip",
    "name": "Gossip",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 38,
    "otherNightReminder": "If the Gossip\u2019s public statement was True: Choose a player not protected from dying tonight. That player dies.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each day, you may make a public statement. Tonight, if it was True, a player dies."
  },
  {
    "id": "courtier",
    "name": "Courtier",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 19,
    "firstNightReminder": "The Courtier either shows a 'no' head signal, or points to a character on the sheet. If the Courtier used their ability: If that character is in play, that player is drunk.",
    "otherNight": 8,
    "otherNightReminder": "Reduce the remaining number of days the marked player is poisoned. If the Courtier has not yet used their ability: The Courtier either shows a 'no' head signal, or points to a character on the sheet. If the Courtier used their ability: If that character is in play, that player is drunk.",
    "reminders": ["Drunk 3",
        "Drunk 2",
        "Drunk 1",
        "No ability"],
    "setup": False,
    "ability": "Once per game, at night, choose a character: they are drunk for 3 nights & 3 days."
  },
  {
    "id": "professor",
    "name": "Professor",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 43,
    "otherNightReminder": "If the Professor has not used their ability: The Professor either shakes their head no, or points to a player. If that player is a Townsfolk, they are now alive.",
    "reminders": ["Alive",
        "No ability"],
    "setup": False,
    "ability": "Once per game, at night*, choose a dead player: if they are a Townsfolk, they are resurrected."
  },
  {
    "id": "minstrel",
    "name": "Minstrel",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Everyone drunk"],
    "setup": False,
    "ability": "When a Minion dies by execution, all other players (except Travellers) are drunk until dusk tomorrow."
  },
  {
    "id": "tealady",
    "name": "Tea Lady",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Can not die"],
    "setup": False,
    "ability": "If both your alive neighbours are good, they can't die."
  },
  {
    "id": "pacifist",
    "name": "Pacifist",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Executed good players might not die."
  },
  {
    "id": "fool",
    "name": "Fool",
    "edition": "bmr",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "The first time you die, you don't."
  },
  {
    "id": "tinker",
    "name": "Tinker",
    "edition": "bmr",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 49,
    "otherNightReminder": "The Tinker might die.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "You might die at any time."
  },
  {
    "id": "moonchild",
    "name": "Moonchild",
    "edition": "bmr",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 50,
    "otherNightReminder": "If the Moonchild used their ability to target a player today: If that player is good, they die.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "When you learn that you died, publicly choose 1 alive player. Tonight, if it was a good player, they die."
  },
  {
    "id": "goon",
    "name": "Goon",
    "edition": "bmr",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Drunk"],
    "setup": False,
    "ability": "Each night, the 1st player to choose you with their ability is drunk until dusk. You become their alignment."
  },
  {
    "id": "lunatic",
    "name": "Lunatic",
    "edition": "bmr",
    "team": "outsider",
    "firstNight": 8,
    "firstNightReminder": "If 7 or more players: Show the Lunatic a number of arbitrary 'Minions', players equal to the number of Minions in play. Show 3 character tokens of arbitrary good characters. If the token received by the Lunatic is a Demon that would wake tonight: Allow the Lunatic to do the Demon actions. Place their 'attack' markers. Wake the Demon. Show the Demon\u2019s real character token. Show them the Lunatic player. If the Lunatic attacked players: Show the real demon each marked player. Remove any Lunatic 'attack' markers.",
    "otherNight": 20,
    "otherNightReminder": "Allow the Lunatic to do the actions of the Demon. Place their 'attack' markers. If the Lunatic selected players: Wake the Demon. Show the 'attack' marker, then point to each marked player. Remove any Lunatic 'attack' markers.",
    "reminders": ["Attack 1",
        "Attack 2",
        "Attack 3"],
    "setup": False,
    "ability": "You think you are a Demon, but you are not. The Demon knows who you are & who you choose at night."
  },
  {
    "id": "godfather",
    "name": "Godfather",
    "edition": "bmr",
    "team": "minion",
    "firstNight": 21,
    "firstNightReminder": "Show each of the Outsider tokens in play.",
    "otherNight": 37,
    "otherNightReminder": "If an Outsider died today: The Godfather points to a player. That player dies.",
    "reminders": ["Died today",
        "Dead"],
    "setup": True,
    "ability": "You start knowing which Outsiders are in play. If 1 died today, choose a player tonight: they die. [\u22121 or +1 Outsider]"
  },
  {
    "id": "devilsadvocate",
    "name": "Devil's Advocate",
    "edition": "bmr",
    "team": "minion",
    "firstNight": 22,
    "firstNightReminder": "The Devil\u2019s Advocate points to a living player. That player survives execution tomorrow.",
    "otherNight": 13,
    "otherNightReminder": "The Devil\u2019s Advocate points to a living player, different from the previous night. That player survives execution tomorrow.",
    "reminders": ["Survives execution"],
    "setup": False,
    "ability": "Each night, choose a living player (different to last night): if executed tomorrow, they don't die."
  },
  {
    "id": "assassin",
    "name": "Assassin",
    "edition": "bmr",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 36,
    "otherNightReminder": "If the Assassin has not yet used their ability: The Assassin either shows the 'no' head signal, or points to a player. That player dies.",
    "reminders": ["Dead",
        "No ability"],
    "setup": False,
    "ability": "Once per game, at night*, choose a player: they die, even if for some reason they could not."
  },
  {
    "id": "mastermind",
    "name": "Mastermind",
    "edition": "bmr",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If the Demon dies by execution (ending the game), play for 1 more day. If a player is then executed, their team loses."
  },
  {
    "id": "zombuul",
    "name": "Zombuul",
    "edition": "bmr",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 25,
    "otherNightReminder": "If no-one died during the day: The Zombuul points to a player. That player dies.",
    "reminders": ["Died today",
        "Dead"],
    "setup": False,
    "ability": "Each night*, if no-one died today, choose a player: they die. The 1st time you die, you live but register as dead."
  },
  {
    "id": "pukka",
    "name": "Pukka",
    "edition": "bmr",
    "team": "demon",
    "firstNight": 28,
    "firstNightReminder": "The Pukka points to a player. That player is poisoned.",
    "otherNight": 26,
    "otherNightReminder": "The Pukka points to a player. That player is poisoned. The previously poisoned player dies. ",
    "reminders": ["Poisoned",
        "Dead"],
    "setup": False,
    "ability": "Each night, choose a player: they are poisoned. The previously poisoned player dies then becomes healthy."
  },
  {
    "id": "shabaloth",
    "name": "Shabaloth",
    "edition": "bmr",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 27,
    "otherNightReminder": "One player that the Shabaloth chose the previous night might be resurrected. The Shabaloth points to two players. Those players die.",
    "reminders": ["Dead",
        "Alive"],
    "setup": False,
    "ability": "Each night*, choose 2 players: they die. A dead player you chose last night might be regurgitated."
  },
  {
    "id": "po",
    "name": "Po",
    "edition": "bmr",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 28,
    "otherNightReminder": "If the Po chose no-one the previous night: The Po points to three players. Otherwise: The Po either shows the 'no' head signal , or points to a player. Chosen players die",
    "reminders": ["Dead",
        "3 attacks"],
    "setup": False,
    "ability": "Each night*, you may choose a player: they die. If your last choice was no-one, choose 3 players tonight."
  },
  {
    "id": "apprentice",
    "name": "Apprentice",
    "edition": "bmr",
    "team": "traveler",
    "firstNight": 1,
    "firstNightReminder": "Show the Apprentice the 'You are' card, then a Townsfolk or Minion token. In the Grimoire, replace the Apprentice token with that character token, and put the Apprentice's 'Is the Apprentice' reminder by that character token.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Is the Apprentice"],
    "setup": False,
    "ability": "On your 1st night, you gain a Townsfolk ability (if good), or a Minion ability (if evil)."
  },
  {
    "id": "matron",
    "name": "Matron",
    "edition": "bmr",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Each day, you may choose up to 3 sets of 2 players to swap seats. Players may not leave their seats to talk in private."
  },
  {
    "id": "judge",
    "name": "Judge",
    "edition": "bmr",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, if another player nominated, you may choose to force the current execution to pass or fail."
  },
  {
    "id": "bishop",
    "name": "Bishop",
    "edition": "bmr",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Nominate good",
        "Nominate evil"],
    "setup": False,
    "ability": "Only the Storyteller can nominate. At least 1 opposite player must be nominated each day."
  },
  {
    "id": "voudon",
    "name": "Voudon",
    "edition": "bmr",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Only you and the dead can vote. They don't need a vote token to do so. A 50% majority is not required."
  },
  {
    "id": "clockmaker",
    "name": "Clockmaker",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 41,
    "firstNightReminder": "Show the hand signal for the number (1, 2, 3, etc.) of places from Demon to closest Minion.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "You start knowing how many steps from the Demon to its nearest Minion."
  },
  {
    "id": "dreamer",
    "name": "Dreamer",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 42,
    "firstNightReminder": "The Dreamer points to a player. Show 1 good and 1 evil character token; one of these is correct.",
    "otherNight": 56,
    "otherNightReminder": "The Dreamer points to a player. Show 1 good and 1 evil character token; one of these is correct.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, choose a player (not yourself or Travellers): you learn 1 good and 1 evil character, 1 of which is correct."
  },
  {
    "id": "snakecharmer",
    "name": "Snake Charmer",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 20,
    "firstNightReminder": "The Snake Charmer points to a player. If that player is the Demon: swap the Demon and Snake Charmer character and alignments. Wake each player to inform them of their new role and alignment. The new Snake Charmer is poisoned.",
    "otherNight": 11,
    "otherNightReminder": "The Snake Charmer points to a player. If that player is the Demon: swap the Demon and Snake Charmer character and alignments. Wake each player to inform them of their new role and alignment. The new Snake Charmer is poisoned.",
    "reminders": ["Poisoned"],
    "setup": False,
    "ability": "Each night, choose an alive player: a chosen Demon swaps characters & alignments with you & is then poisoned."
  },
  {
    "id": "mathematician",
    "name": "Mathematician",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 52,
    "firstNightReminder": "Show the hand signal for the number (0, 1, 2, etc.) of players whose ability malfunctioned due to other abilities.",
    "otherNight": 71,
    "otherNightReminder": "Show the hand signal for the number (0, 1, 2, etc.) of players whose ability malfunctioned due to other abilities.",
    "reminders": ["Abnormal"],
    "setup": False,
    "ability": "Each night, you learn how many players\u2019 abilities worked abnormally (since dawn) due to another character's ability."
  },
  {
    "id": "flowergirl",
    "name": "Flowergirl",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 57,
    "otherNightReminder": "Nod 'yes' or shake head 'no' for whether the Demon voted today. Place the 'Demon not voted' marker (remove 'Demon voted', if any).",
    "reminders": ["Demon voted",
        "Demon not voted"],
    "setup": False,
    "ability": "Each night*, you learn if a Demon voted today."
  },
  {
    "id": "towncrier",
    "name": "Town Crier",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 58,
    "otherNightReminder": "Nod 'yes' or shake head 'no' for whether a Minion nominated today. Place the 'Minion not nominated' marker (remove 'Minion nominated', if any).",
    "reminders": ["Minions not nominated",
        "Minion nominated"],
    "setup": False,
    "ability": "Each night*, you learn if a Minion nominated today."
  },
  {
    "id": "oracle",
    "name": "Oracle",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 59,
    "otherNightReminder": "Show the hand signal for the number (0, 1, 2, etc.) of dead evil players.",
    "reminders": [],
    "setup": False,
    "ability": "Each night*, you learn how many dead players are evil."
  },
  {
    "id": "savant",
    "name": "Savant",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Each day, you may visit the Storyteller to learn 2 things in private: 1 is True & 1 is False."
  },
  {
    "id": "seamstress",
    "name": "Seamstress",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 43,
    "firstNightReminder": "The Seamstress either shows a 'no' head signal, or points to two other players. If the Seamstress chose players , nod 'yes' or shake 'no' for whether they are of same alignment.",
    "otherNight": 60,
    "otherNightReminder": "If the Seamstress has not yet used their ability: the Seamstress either shows a 'no' head signal, or points to two other players. If the Seamstress chose players , nod 'yes' or shake 'no' for whether they are of same alignment.",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, at night, choose 2 players (not yourself): you learn if they are the same alignment."
  },
  {
    "id": "philosopher",
    "name": "Philosopher",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 2,
    "firstNightReminder": "The Philosopher either shows a 'no' head signal, or points to a good character on their sheet. If they chose a character: Swap the out-of-play character token with the Philosopher token and add the 'Is the Philosopher' reminder. If the character is in play, place the drunk marker by that player.",
    "otherNight": 2,
    "otherNightReminder": "If the Philosopher has not used their ability: the Philosopher either shows a 'no' head signal, or points to a good character on their sheet. If they chose a character: Swap the out-of-play character token with the Philosopher token and add the 'Is the Philosopher' reminder. If the character is in play, place the drunk marker by that player.",
    "reminders": ["Drunk",
        "Is the Philosopher"],
    "setup": False,
    "ability": "Once per game, at night, choose a good character: gain that ability. If this character is in play, they are drunk."
  },
  {
    "id": "artist",
    "name": "Artist",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, during the day, privately ask the Storyteller any yes/no question."
  },
  {
    "id": "juggler",
    "name": "Juggler",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 61,
    "otherNightReminder": "If today was the Juggler\u2019s first day: Show the hand signal for the number (0, 1, 2, etc.) of 'Correct' markers. Remove markers.",
    "reminders": ["Correct"],
    "setup": False,
    "ability": "On your 1st day, publicly guess up to 5 players' characters. That night, you learn how many you got correct."
  },
  {
    "id": "sage",
    "name": "Sage",
    "edition": "snv",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 42,
    "otherNightReminder": "If the Sage was killed by a Demon: Point to two players, one of which is that Demon.",
    "reminders": [],
    "setup": False,
    "ability": "If the Demon kills you, you learn that it is 1 of 2 players."
  },
  {
    "id": "mutant",
    "name": "Mutant",
    "edition": "snv",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If you are \u201Cmad\u201D about being an Outsider, you might be executed."
  },
  {
    "id": "sweetheart",
    "name": "Sweetheart",
    "edition": "snv",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 41,
    "otherNightReminder": "Choose a player that is drunk.",
    "reminders": ["Drunk"],
    "setup": False,
    "ability": "When you die, 1 player is drunk from now on."
  },
  {
    "id": "barber",
    "name": "Barber",
    "edition": "snv",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 40,
    "otherNightReminder": "If the Barber died today: Wake the Demon. Show the 'This character selected you' card, then Barber token. The Demon either shows a 'no' head signal, or points to 2 players. If they chose players: Swap the character tokens. Wake each player. Show 'You are', then their new character token.",
    "reminders": ["Haircuts tonight"],
    "setup": False,
    "ability": "If you died today or tonight, the Demon may choose 2 players (not another Demon) to swap characters."
  },
  {
    "id": "klutz",
    "name": "Klutz",
    "edition": "snv",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "When you learn that you died, publicly choose 1 alive player: if they are evil, your team loses."
  },
  {
    "id": "eviltwin",
    "name": "Evil Twin",
    "edition": "snv",
    "team": "minion",
    "firstNight": 23,
    "firstNightReminder": "Wake the Evil Twin and their twin. Confirm that they have acknowledged each other. Point to the Evil Twin. Show their Evil Twin token to the twin player. Point to the twin. Show their character token to the Evil Twin player.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Twin"],
    "setup": False,
    "ability": "You & an opposing player know each other. If the good player is executed, evil wins. Good can't win if you both live."
  },
  {
    "id": "witch",
    "name": "Witch",
    "edition": "snv",
    "team": "minion",
    "firstNight": 24,
    "firstNightReminder": "The Witch points to a player. If that player nominates tomorrow they die immediately.",
    "otherNight": 14,
    "otherNightReminder": "If there are 4 or more players alive: The Witch points to a player. If that player nominates tomorrow they die immediately.",
    "reminders": ["Cursed"],
    "setup": False,
    "ability": "Each night, choose a player: if they nominate tomorrow, they die. If just 3 players live, you lose this ability."
  },
  {
    "id": "cerenovus",
    "name": "Cerenovus",
    "edition": "snv",
    "team": "minion",
    "firstNight": 25,
    "firstNightReminder": "The Cerenovus points to a player, then to a character on their sheet. Wake that player. Show the 'This character selected you' card, then the Cerenovus token. Show the selected character token. If the player is not mad about being that character tomorrow, they can be executed.",
    "otherNight": 15,
    "otherNightReminder": "The Cerenovus points to a player, then to a character on their sheet. Wake that player. Show the 'This character selected you' card, then the Cerenovus token. Show the selected character token. If the player is not mad about being that character tomorrow, they can be executed.",
    "reminders": ["Mad"],
    "setup": False,
    "ability": "Each night, choose a player & a good character: they are \u201Cmad\u201D they are this character tomorrow, or might be executed."
  },
  {
    "id": "pithag",
    "name": "Pit-Hag",
    "edition": "snv",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 16,
    "otherNightReminder": "The Pit-Hag points to a player and a character on the sheet. If this character is not in play, wake that player and show them the 'You are' card and the relevant character token. If the character is in play, nothing happens.",
    "reminders": [],
    "setup": False,
    "ability": "Each night*, choose a player & a character they become (if not-in-play). If a Demon is made, deaths tonight are arbitrary."
  },
  {
    "id": "fanggu",
    "name": "Fang Gu",
    "edition": "snv",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 29,
    "otherNightReminder": "The Fang Gu points to a player. That player dies. Or, if that player was an Outsider and there are no other Fang Gu in play: The Fang Gu dies instead of the chosen player. The chosen player is now an evil Fang Gu. Wake the new Fang Gu. Show the 'You are' card, then the Fang Gu token. Show the 'You are' card, then the thumb-down 'evil' hand sign.",
    "reminders": ["Dead",
        "Once"],
    "setup": True,
    "ability": "Each night*, choose a player: they die. The 1st Outsider this kills becomes an evil Fang Gu & you die instead. [+1 Outsider]"
  },
  {
    "id": "vigormortis",
    "name": "Vigormortis",
    "edition": "snv",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 32,
    "otherNightReminder": "The Vigormortis points to a player. That player dies. If a Minion, they keep their ability and one of their Townsfolk neighbours is poisoned.",
    "reminders": ["Dead",
        "Has ability",
        "Poisoned"],
    "setup": True,
    "ability": "Each night*, choose a player: they die. Minions you kill keep their ability & poison 1 Townsfolk neighbour. [\u22121 Outsider]"
  },
  {
    "id": "nodashii",
    "name": "No Dashii",
    "edition": "snv",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 30,
    "otherNightReminder": "The No Dashii points to a player. That player dies.",
    "reminders": ["Dead",
        "Poisoned"],
    "setup": False,
    "ability": "Each night*, choose a player: they die. Your 2 Townsfolk neighbours are poisoned."
  },
  {
    "id": "vortox",
    "name": "Vortox",
    "edition": "snv",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 31,
    "otherNightReminder": "The Vortox points to a player. That player dies.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each night*, choose a player: they die. Townsfolk abilities yield False info. Each day, if no-one is executed, evil wins."
  },
  {
    "id": "barista",
    "name": "Barista",
    "edition": "snv",
    "team": "traveler",
    "firstNight": 1,
    "firstNightReminder": "Choose a player, wake them and tell them which Barista power is affecting them. Treat them accordingly (sober/healthy/True info or activate their ability twice).",
    "otherNight": 1,
    "otherNightReminder": "Choose a player, wake them and tell them which Barista power is affecting them. Treat them accordingly (sober/healthy/True info or activate their ability twice).",
    "reminders": ["Sober & Healthy",
        "Ability twice"],
    "setup": False,
    "ability": "Each night, until dusk, 1) a player becomes sober, healthy and gets True info, or 2) their ability works twice. They learn which."
  },
  {
    "id": "harlot",
    "name": "Harlot",
    "edition": "snv",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 1,
    "otherNightReminder": "The Harlot points at any player. Then, put the Harlot to sleep. Wake the chosen player, show them the 'This character selected you' token, then the Harlot token. That player either nods their head yes or shakes their head no. If they nodded their head yes, wake the Harlot and show them the chosen player's character token. Then, you may decide that both players die.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each night*, choose a living player: if they agree, you learn their character, but you both might die."
  },
  {
    "id": "butcher",
    "name": "Butcher",
    "edition": "snv",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Each day, after the 1st execution, you may nominate again."
  },
  {
    "id": "bonecollector",
    "name": "Bone Collector",
    "edition": "snv",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 1,
    "otherNightReminder": "The Bone Collector either shakes their head no or points at any dead player. If they pointed at any dead player, put the Bone Collector's 'Has Ability' reminder by the chosen player's character token. (They may need to be woken tonight to use it.)",
    "reminders": ["No ability",
        "Has ability"],
    "setup": False,
    "ability": "Once per game, at night, choose a dead player: they regain their ability until dusk."
  },
  {
    "id": "deviant",
    "name": "Deviant",
    "edition": "snv",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If you were funny today, you cannot die by exile."
  },
  {
    "id": "noble",
    "name": "Noble",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 44,
    "firstNightReminder": "Point to 3 players including one evil player, in no particular order.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Seen"],
    "setup": False,
    "ability": "You start knowing 3 players, 1 and only 1 of which is evil."
  },
  {
    "id": "bountyhunter",
    "name": "Bounty Hunter",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 46,
    "firstNightReminder": "Point to 1 evil player. Wake the townsfolk who is evil and show them the 'You are' card and the thumbs down evil sign.",
    "otherNight": 64,
    "otherNightReminder": "If the known evil player has died, point to another evil player. ",
    "reminders": ["Known"],
    "setup": True,
    "ability": "You start knowing 1 evil player. If the player you know dies, you learn another evil player tonight. [1 Townsfolk is evil]"
  },
  {
    "id": "pixie",
    "name": "Pixie",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 29,
    "firstNightReminder": "Show the Pixie 1 in-play Townsfolk character token.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Mad",
        "Has ability"],
    "setup": False,
    "ability": "You start knowing 1 in-play Townsfolk. If you were mad that you were this character, you gain their ability when they die."
  },
  {
    "id": "general",
    "name": "General",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 50,
    "firstNightReminder": "Show the General thumbs up for good winning, thumbs down for evil winning or thumb to the side for neither.",
    "otherNight": 69,
    "otherNightReminder": "Show the General thumbs up for good winning, thumbs down for evil winning or thumb to the side for neither.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, you learn which alignment the Storyteller believes is winning: good, evil, or neither."
  },
  {
    "id": "preacher",
    "name": "Preacher",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 14,
    "firstNightReminder": "The Preacher chooses a player. If a Minion is chosen, wake the Minion and show the 'This character selected you' card and then the Preacher token.",
    "otherNight": 6,
    "otherNightReminder": "The Preacher chooses a player. If a Minion is chosen, wake the Minion and show the 'This character selected you' card and then the Preacher token.",
    "reminders": ["At a sermon"],
    "setup": False,
    "ability": "Each night, choose a player: a Minion, if chosen, learns this. All chosen Minions have no ability."
  },
  {
    "id": "king",
    "name": "King",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 10,
    "firstNightReminder": "Wake the Demon, show them the 'This character selected you' card, show the King token and point to the King player.",
    "otherNight": 63,
    "otherNightReminder": "If there are more dead than living, show the King a character token of a living player.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, if the dead outnumber the living, you learn 1 alive character. The Demon knows who you are."
  },
  {
    "id": "balloonist",
    "name": "Balloonist",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 45,
    "firstNightReminder": "Choose a character type. Point to a player whose character is of that type. Place the Balloonist's Seen reminder next to that character.",
    "otherNight": 62,
    "otherNightReminder": "Choose a character type that does not yet have a Seen reminder next to a character of that type. Point to a player whose character is of that type, if there are any. Place the Balloonist's Seen reminder next to that character.",
    "reminders": ["Seen Townsfolk",
        "Seen Outsider",
        "Seen Minion",
        "Seen Demon",
        "Seen Traveller"],
    "setup": True,
    "ability": "Each night, you learn 1 player of each character type, until there are no more types to learn. [+1 Outsider]"
  },
  {
    "id": "cultleader",
    "name": "Cult Leader",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 48,
    "firstNightReminder": "If the cult leader changed alignment, show them the thumbs up good signal of the thumbs down evil signal accordingly.",
    "otherNight": 66,
    "otherNightReminder": "If the cult leader changed alignment, show them the thumbs up good signal of the thumbs down evil signal accordingly.",
    "reminders": [],
    "setup": False,
    "ability": "Each night, you become the alignment of an alive neighbour. If all good players choose to join your cult, your team wins."
  },
  {
    "id": "lycanthrope",
    "name": "Lycanthrope",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 22,
    "otherNightReminder": "The Lycanthrope points to a living player: if good, they die and no one else can die tonight.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each night*, choose a living player: if good, they die, but they are the only player that can die tonight."
  },
  {
    "id": "amnesiac",
    "name": "Amnesiac",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 32,
    "firstNightReminder": "Decide the Amnesiac's entire ability. If the Amnesiac's ability causes them to wake tonight: Wake the Amnesiac and run their ability.",
    "otherNight": 47,
    "otherNightReminder": "If the Amnesiac's ability causes them to wake tonight: Wake the Amnesiac and run their ability.",
    "reminders": ["?"],
    "setup": False,
    "ability": "You do not know what your ability is. Each day, privately guess what it is: you learn how accurate you are."
  },
  {
    "id": "nightwatchman",
    "name": "Nightwatchman",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 47,
    "firstNightReminder": "The Nightwatchman may point to a player. Wake that player, show the 'This character selected you' card and the Nightwatchman token, then point to the Nightwatchman player.",
    "otherNight": 65,
    "otherNightReminder": "The Nightwatchman may point to a player. Wake that player, show the 'This character selected you' card and the Nightwatchman token, then point to the Nightwatchman player.",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, at night, choose a player: they learn who you are."
  },
  {
    "id": "engineer",
    "name": "Engineer",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 13,
    "firstNightReminder": "The Engineer shows a 'no' head signal, or points to a Demon or points to the relevant number of Minions. If the Engineer chose characters, replace the Demon or Minions with the choices, then wake the relevant players and show them the You are card and the relevant character tokens.",
    "otherNight": 5,
    "otherNightReminder": "The Engineer shows a 'no' head signal, or points to a Demon or points to the relevant number of Minions. If the Engineer chose characters, replace the Demon or Minions with the choices, then wake the relevant players and show them the 'You are' card and the relevant character tokens.",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, at night, choose which Minions or which Demon is in play."
  },
  {
    "id": "fisherman",
    "name": "Fisherman",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["No ability"],
    "setup": False,
    "ability": "Once per game, during the day, visit the Storyteller for some advice to help you win."
  },
  {
    "id": "huntsman",
    "name": "Huntsman",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 30,
    "firstNightReminder": "The Huntsman shakes their head 'no' or points to a player. If they point to the Damsel, wake that player, show the 'You are' card and a not-in-play character token.",
    "otherNight": 45,
    "otherNightReminder": "The Huntsman shakes their head 'no' or points to a player. If they point to the Damsel, wake that player, show the 'You are' card and a not-in-play character token.",
    "reminders": ["No ability"],
    "setup": True,
    "ability": "Once per game, at night, choose a living player: the Damsel, if chosen, becomes a not-in-play Townsfolk. [+the Damsel]"
  },
  {
    "id": "alchemist",
    "name": "Alchemist",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 3,
    "firstNightReminder": "Show the Alchemist a not-in-play Minion token",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "remindersGlobal": ["Is the Alchemist"],
    "setup": False,
    "ability": "You have a not-in-play Minion ability."
  },
  {
    "id": "farmer",
    "name": "Farmer",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 48,
    "otherNightReminder": "If a Farmer died tonight, choose another good player and make them the Farmer. Wake this player, show them the 'You are' card and the Farmer character token.",
    "reminders": [],
    "setup": False,
    "ability": "If you die at night, an alive good player becomes a Farmer."
  },
  {
    "id": "magician",
    "name": "Magician",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 5,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "The Demon thinks you are a Minion. Minions think you are a Demon."
  },
  {
    "id": "choirboy",
    "name": "Choirboy",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 44,
    "otherNightReminder": "If the King was killed by the Demon, wake the Choirboy and point to the Demon player.",
    "reminders": [],
    "setup": True,
    "ability": "If the Demon kills the King, you learn which player is the Demon. [+ the King]"
  },
  {
    "id": "poppygrower",
    "name": "Poppy Grower",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 4,
    "firstNightReminder": "Do not inform the Demon/Minions who each other are",
    "otherNight": 3,
    "otherNightReminder": "If the Poppy Grower has died, show the Minions/Demon who each other are.",
    "reminders": ["Evil wakes"],
    "setup": False,
    "ability": "Minions & Demons do not know each other. If you die, they learn who each other are that night."
  },
  {
    "id": "atheist",
    "name": "Atheist",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": True,
    "ability": "The Storyteller can break the game rules & if executed, good wins, even if you are dead. [No evil characters]"
  },
  {
    "id": "cannibal",
    "name": "Cannibal",
    "edition": "",
    "team": "townsfolk",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Poisoned",
        "Died today"],
    "setup": False,
    "ability": "You have the ability of the recently killed executee. If they are evil, you are poisoned until a good player dies by execution."
  },
  {
    "id": "snitch",
    "name": "Snitch",
    "edition": "",
    "team": "outsider",
    "firstNight": 7,
    "firstNightReminder": "After Minion info wake each Minion and show them three not-in-play character tokens. These may be the same or different to each other and the ones shown to the Demon.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Minions start knowing 3 not-in-play characters."
  },
  {
    "id": "acrobat",
    "name": "Acrobat",
    "edition": "",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 39,
    "otherNightReminder": "If a good living neighbour is drunk or poisoned, the Acrobat player dies.",
    "reminders": ["Dead"],
    "setup": False,
    "ability": "Each night*, if either good living neighbour is drunk or poisoned, you die."
  },
  {
    "id": "puzzlemaster",
    "name": "Puzzlemaster",
    "edition": "",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Drunk",
        "Guess used"],
    "setup": False,
    "ability": "1 player is drunk, even if you die. If you guess (once) who it is, learn the Demon player, but guess wrong & get False info."
  },
  {
    "id": "heretic",
    "name": "Heretic",
    "edition": "",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Whoever wins, loses & whoever loses, wins, even if you are dead."
  },
  {
    "id": "damsel",
    "name": "Damsel",
    "edition": "",
    "team": "outsider",
    "firstNight": 31,
    "firstNightReminder": "Wake all the Minions, show them the 'This character selected you' card and the Damsel token.",
    "otherNight": 46,
    "otherNightReminder": "If selected by the Huntsman, wake the Damsel, show 'You are' card and a not-in-play Townsfolk token.",
    "reminders": ["Guess used"],
    "setup": False,
    "ability": "All Minions know you are in play. If a Minion publicly guesses you (once), your team loses."
  },
  {
    "id": "golem",
    "name": "Golem",
    "edition": "",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Can not nominate"],
    "setup": False,
    "ability": "You may only nominate once per game. When you do, if the nominee is not the Demon, they die."
  },
  {
    "id": "politician",
    "name": "Politician",
    "edition": "",
    "team": "outsider",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If you were the player most responsible for your team losing, you change alignment & win, even if dead."
  },
  {
    "id": "widow",
    "name": "Widow",
    "edition": "",
    "team": "minion",
    "firstNight": 18,
    "firstNightReminder": "Show the Grimoire to the Widow for as long as they need. The Widow points to a player. That player is poisoned. Wake a good player. Show the 'These characters are in play' card, then the Widow character token.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Poisoned"],
    "remindersGlobal": ["Knows"],
    "setup": False,
    "ability": "On your 1st night, look at the Grimoire and choose a player: they are poisoned. 1 good player knows a Widow is in play."
  },
  {
    "id": "fearmonger",
    "name": "Fearmonger",
    "edition": "",
    "team": "minion",
    "firstNight": 26,
    "firstNightReminder": "The Fearmonger points to a player. Place the Fear token next to that player and announce that a new player has been selected with the Fearmonger ability.",
    "otherNight": 17,
    "otherNightReminder": "The Fearmonger points to a player. If different from the previous night, place the Fear token next to that player and announce that a new player has been selected with the Fearmonger ability.",
    "reminders": ["Fear"],
    "setup": False,
    "ability": "Each night, choose a player. If you nominate & execute them, their team loses. All players know if you choose a new player."
  },
  {
    "id": "psychopath",
    "name": "Psychopath",
    "edition": "",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Each day, before nominations, you may publicly choose a player: they die. If executed, you only die if you lose roshambo."
  },
  {
    "id": "goblin",
    "name": "Goblin",
    "edition": "",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": ["Claimed"],
    "setup": False,
    "ability": "If you publicly claim to be the Goblin when nominated & are executed that day, your team wins."
  },
  {
    "id": "mephit",
    "name": "Mephit",
    "edition": "",
    "team": "minion",
    "firstNight": 27,
    "firstNightReminder": "Show the Mephit their secret word.",
    "otherNight": 18,
    "otherNightReminder": "Wake the 1st good player that said the Mephit's secret word and show them the 'You are' card and the thumbs down evil signal.",
    "reminders": ["Turns evil",
        "No ability"],
    "setup": False,
    "ability": "You start knowing a secret word. The 1st good player to say this word becomes evil that night."
  },
  {
    "id": "mezepheles",
    "name": "Mezepheles",
    "edition": "",
    "team": "minion",
    "firstNight": 27,
    "firstNightReminder": "Show the Mezepheles their secret word.",
    "otherNight": 18,
    "otherNightReminder": "Wake the 1st good player that said the Mezepheles' secret word and show them the 'You are' card and the thumbs down evil signal.",
    "reminders": ["Turns evil",
        "No ability"],
    "setup": False,
    "ability": "You start knowing a secret word. The 1st good player to say this word becomes evil that night."
  },
  {
    "id": "marionette",
    "name": "Marionette",
    "edition": "",
    "team": "minion",
    "firstNight": 12,
    "firstNightReminder": "Select one of the good players next to the Demon and place the Is the Marionette reminder token. Wake the Demon and show them the Marionette.",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "remindersGlobal": ["Is the Marionette"],
    "setup": True,
    "ability": "You think you are a good character but you are not. The Demon knows who you are. [You neighbour the Demon]"
  },
  {
    "id": "boomdandy",
    "name": "Boomdandy",
    "edition": "",
    "team": "minion",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "If you are executed, all but 3 players die. 1 minute later, the player with the most players pointing at them dies."
  },
  {
    "id": "lilmonsta",
    "name": "Lil' Monsta",
    "edition": "",
    "team": "demon",
    "firstNight": 15,
    "firstNightReminder": "Wake all Minions together, allow them to vote by pointing at who they want to babysit Lil' Monsta.",
    "otherNight": 35,
    "otherNightReminder": "Wake all Minions together, allow them to vote by pointing at who they want to babysit Lil' Monsta. Choose a player, that player dies.",
    "reminders": [],
    "remindersGlobal": ["Is the Demon",
        "Dead"],
    "setup": True,
    "ability": "Each night, Minions choose who babysits Lil' Monsta's token & \"is the Demon\". A player dies each night*. [+1 Minion]"
  },
  {
    "id": "lleech",
    "name": "Lleech",
    "edition": "",
    "team": "demon",
    "firstNight": 16,
    "firstNightReminder": "The Lleech points to a player. Place the Poisoned reminder token.",
    "otherNight": 34,
    "otherNightReminder": "The Lleech points to a player. That player dies.",
    "reminders": ["Dead",
        "Poisoned"],
    "setup": False,
    "ability": "Each night*, choose a player: they die. You start by choosing an alive player: they are poisoned - you die if & only if they die."
  },
  {
    "id": "alhadikhia",
    "name": "Al-Hadikhia",
    "edition": "",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 33,
    "otherNightReminder": "The Al-Hadikhia chooses 3 players. Announce the first player, wake them to nod yes to live or shake head no to die, kill or resurrect accordingly, then put to sleep and announce the next player. If all 3 are alive after this, all 3 die.",
    "reminders": ["1", "2", "3",
        "Chose death",
        "Chose life"],
    "setup": False,
    "ability": "Each night*, choose 3 players (all players learn who): each silently chooses to live or die, but if all live, all die."
  },
  {
    "id": "legion",
    "name": "Legion",
    "edition": "",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 23,
    "otherNightReminder": "Choose a player, that player dies.",
    "reminders": ["Dead",
        "About to die"],
    "setup": True,
    "ability": "Each night*, a player might die. Executions fail if only evil voted. You register as a Minion too. [Most players are Legion]"
  },
  {
    "id": "leviathan",
    "name": "Leviathan",
    "edition": "",
    "team": "demon",
    "firstNight": 54,
    "firstNightReminder": "Place the Leviathan 'Day 1' marker. Announce 'The Leviathan is in play; this is Day 1.'",
    "otherNight": 73,
    "otherNightReminder": "Change the Leviathan Day reminder for the next day.",
    "reminders": ["Day 1",
        "Day 2",
        "Day 3",
        "Day 4",
        "Day 5",
        "Good player executed"],
    "setup": False,
    "ability": "If more than 1 good player is executed, you win. All players know you are in play. After day 5, evil wins."
  },
  {
    "id": "riot",
    "name": "Riot",
    "edition": "",
    "team": "demon",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": True,
    "ability": "Nominees die, but may nominate again immediately (on day 3, they must). After day 3, evil wins. [All Minions are Riot]"
  },
  {
    "id": "gangster",
    "name": "Gangster",
    "edition": "",
    "team": "traveler",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNight": 0,
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "ability": "Once per day, you may choose to kill an alive neighbour, if your other alive neighbour agrees."
  }
]


hatred = [
  {
    "id": "Chambermaid",
    "hatred": [
      {
        "id": "Mathematician",
        "reason": "The Chambermaid learns if the Mathematician wakes tonight or not, even though the Chambermaid wakes first."
      }
    ]
  },
  {
    "id": "Butler",
    "hatred": [
      {
        "id": "Cannibal",
        "reason": "If the Cannibal gains the Butler ability, the Cannibal learns this."
      }
    ]
  },
  {
    "id": "Lunatic",
    "hatred": [
      {
        "id": "Mathematician",
        "reason": "The Mathematician learns if the Lunatic attacks a different player(s) than the real Demon attacked."
      }
    ]
  },
  {
    "id": "Pit-Hag",
    "hatred": [
      {
        "id": "Heretic",
        "reason": "A Pit-Hag can not create a Heretic. "
      },
      {
        "id": "Damsel",
        "reason": "If a Pit-Hag creates a Damsel, the Storyteller chooses which player it is."
      },
      {
        "id": "Politician",
        "reason": "A Pit-hag can not create an evil Politician."
      }
    ]
  },
  {
    "id": "Cerenovus",
    "hatred": [
      {
        "id": "Goblin",
        "reason": "The Cerenovus may choose to make a player mad that they are the Goblin."
      }
    ]
  },
  {
    "id": "Leviathan",
    "hatred": [
      {
        "id": "Soldier",
        "reason": "If Leviathan nominates and executes the Soldier, the Soldier does not die."
      },
      {
        "id": "Monk",
        "reason": "If Leviathan nominates and executes the player the Monk chose, that player does not die."
      },
      {
        "id": "Innkeeper",
        "reason": "If Leviathan nominates and executes a player the Innkeeper chose, that player does not die."
      },
      {
        "id": "Ravenkeeper",
        "reason": "If Leviathan is in play & the Ravenkeeper dies by execution, they wake that night to use their ability."
      },
      {
        "id": "Sage",
        "reason": "If Leviathan is in play & the Sage dies by execution, they wake that night to use their ability."
      },
      {
        "id": "Farmer",
        "reason": "If Leviathan is in play & a Farmer dies by execution, a good player becomes a Farmer that night."
      },
      {
        "id": "Mayor",
        "reason": "If Leviathan is in play & no execution occurs on day 5, good wins."
      }
    ]
  },
  {
    "id": "Al-Hadikhia",
    "hatred": [
      {
        "id": "Scarlet Woman",
        "reason": "If there are two living Al-Hadikhias, the Scarlet Woman Al-Hadikhia becomes the Scarlet Woman again."
      },
      {
        "id": "Mastermind",
        "reason": "Only 1 jinxed character can be in play. Evil players start knowing which player and character it is."
      }
    ]
  },
  {
    "id": "Lil' Monsta",
    "hatred": [
      {
        "id": "Poppy Grower",
        "reason": "If the Poppy Grower is in play, Minions don't wake together. They are woken one by one, until one of them chooses to take the Lil' Monsta token."
      },
      {
        "id": "Magician",
        "reason": "Only 1 jinxed character can be in play. "
      },
      {
        "id": "Scarlet Woman",
        "reason": "If there are 5 or more players alive and the player holding the Lil' Monsta token dies, the Scarlet Woman is given the Lil' Monsta token tonight."
      }
    ]
  },
  {
    "id": "Lycanthrope",
    "hatred": [
      {
        "id": "Gambler",
        "reason": "If the Lycanthrope is alive and the Gambler kills themself at night, no other players can die tonight."
      }
    ]
  },
  {
    "id": "Legion",
    "hatred": [
      {
        "id": "Engineer",
        "reason": "Legion and the Engineer can not both be in play at the start of the game. If the Engineer creates Legion, most players (including all evil players) become evil Legion."
      },
      {
        "id": "Preacher",
        "reason": "Only 1 jinxed character can be in play."
      }
    ]
  },
  {
    "id": "Fang Gu",
    "hatred": [
      {
        "id": "Scarlet Woman",
        "reason": "If the Fang Gu chooses an Outsider and dies, the Scarlet Woman does not become the Fang Gu."
      }
    ]
  },
  {
    "id": "Spy",
    "hatred": [
      {
        "id": "Magician",
        "reason": "When the Spy sees the Grimoire, the Demon and Magician's character tokens are removed."
      },
      {
        "id": "Alchemist",
        "reason": "The Alchemist can not have the Spy ability."
      },
      {
        "id": "Poppy Grower",
        "reason": "If the Poppy Grower is in play, the Spy does not see the Grimoire until the Poppy Grower dies."
      },
      {
        "id": "Damsel",
        "reason": "Only 1 jinxed character can be in play. "
      },
      {
        "id": "Heretic",
        "reason": "Only 1 jinxed character can be in play."
      }
    ]
  },
  {
    "id": "Widow",
    "hatred": [
      {
        "id": "Magician",
        "reason": "When the Widow sees the Grimoire, the Demon and Magician's character tokens are removed."
      },
      {
        "id": "Poppy Grower",
        "reason": "If the Poppy Grower is in play, the Widow does not see the Grimoire until the Poppy Grower dies."
      },
      {
        "id": "Alchemist",
        "reason": "The Alchemist can not have the Widow ability."
      },
      {
        "id": "Damsel",
        "reason": "Only 1 jinxed character can be in play."
      },
      {
        "id": "Heretic",
        "reason": "Only 1 jinxed character can be in play."
      }
    ]
  },
  {
    "id": "Godfather",
    "hatred": [
      {
        "id": "Heretic",
        "reason": "Only 1 jinxed character can be in play."
      }
    ]
  },
  {
    "id": "Baron",
    "hatred": [
      {
        "id": "Heretic",
        "reason": "The Baron might only add 1 Outsider, not 2."
      }
    ]
  },
  {
    "id": "Marionette",
    "hatred": [
      {
        "id": "Lil' Monsta",
        "reason": "The Marionette neighbors a Minion, not the Demon. The Marionette is not woken to choose who takes the Lil' Monsta token."
      },
      {
        "id": "Poppy Grower",
        "reason": "When the Poppy Grower dies, the Demon learns the Marionette but the Marionette learns nothing."
      },
      {
        "id": "Snitch",
        "reason": "The Marionette does not learn 3 not in-play characters. The Demon learns an extra 3 instead."
      },
      {
        "id": "Balloonist",
        "reason": "If the Marionette thinks that they are the Balloonist, +1 Outsider was added."
      },
      {
        "id": "Damsel",
        "reason": "The Marionette does not learn that a Damsel is in play."
      },
      {
        "id": "Huntsman",
        "reason": "If the Marionette thinks that they are the Huntsman, the Damsel was added."
      }
    ]
  },
  {
    "id": "Riot",
    "hatred": [
      {
        "id": "Engineer",
        "reason": "Riot and the Engineer can not both be in play at the start of the game. \nIf the Engineer creates Riot, the evil players become Riot."
      },
      {
        "id": "Golem",
        "reason": "If The Golem nominates Riot, the Riot player does not die."
      },
      {
        "id": "Snitch",
        "reason": "If the Snitch is in play, each Riot player gets an extra 3 bluffs."
      },
      {
        "id": "Saint",
        "reason": "If a good player nominates and kills the Saint, the Saint's team loses."
      },
      {
        "id": "Butler",
        "reason": "The Butler can not nominate their master."
      },
      {
        "id": "Pit-Hag",
        "reason": "If the Pit-Hag creates Riot, all evil players become Riot. \nIf the Pit-Hag creates Riot after day 3, the game continues for one more day."
      },
      {
        "id": "Mayor",
        "reason": "If the 3rd day begins with just three players alive, the players may choose (as a group) not to nominate at all. If so (and a Mayor is alive) then the Mayor's team wins."
      },
      {
        "id": "Monk",
        "reason": "If a Riot player nominates and kills the Monk-protected-player, the Monk-protected-player does not die."
      },
      {
        "id": "Farmer",
        "reason": "If a Riot player nominates and kills a Farmer, the Farmer uses their ability tonight."
      },
      {
        "id": "Innkeeper",
        "reason": "If a Riot player nominates an Innkeeper-protected-player, the Innkeeper-protected-player does not die."
      },
      {
        "id": "Sage",
        "reason": "If a Riot player nominates and kills a Sage, the Sage uses their ability tonight."
      },
      {
        "id": "Ravenkeeper",
        "reason": "If a Riot player nominates and kills the Ravenkeeper, the Ravenkeeper uses their ability tonight."
      },
      {
        "id": "Soldier",
        "reason": "If a Riot player nominates the Soldier, the Soldier does not die."
      },
      {
        "id": "Grandmother",
        "reason": "If a Riot player nominates and kills the Grandchild, the Grandmother dies too."
      },
      {
        "id": "King",
        "reason": "If a Riot player nominates and kills the King and the Choirboy is alive, the Choirboy uses their ability tonight."
      },
      {
        "id": "Exorcist",
        "reason": "Only 1 jinxed character can be in play."
      },
      {
        "id": "Minstrel",
        "reason": "Only 1 jinxed character can be in play."
      },
      {
        "id": "Flowergirl",
        "reason": "Only 1 jinxed character can be in play."
      },
      {
        "id": "Undertaker",
        "reason": "Players that die by nomination register as being executed to the Undertaker."
      },
      {
        "id": "Cannibal",
        "reason": "Players that die by nomination register as being executed to the Cannibal."
      },
      {
        "id": "Pacifist",
        "reason": "Players that die by nomination register as being executed to the Pacifist."
      },
      {
        "id": "Devil's Advocate",
        "reason": "Players that die by nomination register as being executed to the Devil's Advocate."
      },
      {
        "id": "Investigator",
        "reason": "Riot registers as a Minion to the Investigator."
      },
      {
        "id": "Clockmaker",
        "reason": "Riot registers as a Minion to the Clockmaker."
      },
      {
        "id": "Town Crier",
        "reason": "Riot registers as a Minion to the Town Crier."
      },
      {
        "id": "Damsel",
        "reason": "Riot registers as a Minion to the Damsel."
      },
      {
        "id": "Preacher",
        "reason": "Riot registers as a Minion to the Preacher."
      }
    ]
  },
  {
    "id": "Lleech",
    "hatred": [
      {
        "id": "Mastermind",
        "reason": "If the Mastermind is alive and the Lleech's host dies by execution, the Lleech lives but loses their ability. "
      },
      {
        "id": "Slayer",
        "reason": "If the Slayer slays the Lleech's host, the host dies. "
      },
      {
        "id": "Heretic",
        "reason": "If the Lleech has poisoned the Heretic then the Lleech dies, the Heretic remains poisoned."
      }
    ]
  }
]


editions = [
  {
    "id": "tb",
    "name": "Trouble Brewing",
    "author": "The Pandemonium Institute",
    "description": "Clouds roll in over Ravenswood Bluff, engulfing this sleepy town and its superstitious inhabitants in foreboding shadow. Freshly-washed clothes dance eerily on lines strung between cottages. Chimneys cough plumes of smoke into the air. Exotic scents waft through cracks in windows and under doors, as hidden cauldrons lay bubbling. An unusually warm Autumn breeze wraps around vine-covered walls and whispers ominously to those brave enough to walk the cobbled streets.\n\nAnxious mothers call their children home from play, as thunder begins to clap on the horizon. If you listen more closely, however, noises stranger still can be heard echoing from the neighbouring forest. Under the watchful eye of a looming monastery, silhouetted figures skip from doorway to doorway. Those who can read the signs know there is... Trouble Brewing.",
    "level": "Beginner",
    "roles": [],
    "isOfficial": True
  },
  {
    "id": "bmr",
    "name": "Bad Moon Rising",
    "author": "The Pandemonium Institute",
    "description": "The sun is swallowed by a jagged horizon as another winter's day surrenders to the night. Flecks of orange and red decay into deeper browns, the forest transforming in silent anticipation of the coming snow.\n\nRavenous wolves howl from the bowels of a rocky crevasse beyond the town borders, sending birds scattering from their cozy rooks. Travelers hurry into the inn, seeking shelter from the gathering chill. They warm themselves with hot tea, sweet strains of music and hearty ale, unaware that strange and nefarious eyes stalk them from the ruins of this once great city.\n\nTonight, even the livestock know there is a... Bad Moon Rising.",
    "level": "Intermediate",
    "roles": [],
    "isOfficial": True
  },
  {
    "id": "snv",
    "name": "Sects & Violets",
    "author": "The Pandemonium Institute",
    "description": "Vibrant spring gives way to a warm and inviting summer. Flowers of every description blossom as far as the eye can see, tenderly nurtured in public gardens and window boxes overlooking the lavish promenade. Birds sing, artists paint and philosophers ponder life's greatest mysteries inside a bustling tavern as a circus pitches its endearingly ragged tent on the edge of town.\n\nAs the townsfolk bask in frivolity and mischief, indulging themselves in fine entertainment and even finer wine, dark and clandestine forces are assembling. Witches and cults lurk in majestic ruins on the fringes of the community, hosting secret meetings in underground caves and malevolently plotting the downfall of Ravenswood Bluff and its revelers.\n\nThe time is ripe for... Sects & Violets.",
    "level": "Intermediate",
    "roles": [],
    "isOfficial": True
  },
  {
    "id": "luf",
    "name": "Laissez un Faire",
    "author": "The Pandemonium Institute",
    "description": "",
    "level": "Veteran",
    "roles": ["balloonist", "savant", "amnesiac", "fisherman", "artist", "cannibal", "mutant", "lunatic", "widow", "goblin", "leviathan"],
    "isOfficial": True
  }
]

fabled = [
  {
    "id": "doomsayer",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "name": "Doomsayer",
    "team": "fabled",
    "ability": "If 4 or more players live, each living player may publicly choose (once per game) that a player of their own alignment dies."
  },
  {
    "id": "angel",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": ["Protect", "Something Bad"],
    "setup": False,
    "name": "Angel",
    "team": "fabled",
    "ability": "Something bad might happen to whoever is most responsible for the death of a new player."
  },
  {
    "id": "buddhist",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "name": "Buddhist",
    "team": "fabled",
    "ability": "For the first 2 minutes of each day, veteran players may not talk."
  },
  {
    "id": "hellslibrarian",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": ["Something Bad"],
    "setup": False,
    "name": "Hell's Librarian",
    "team": "fabled",
    "ability": "Something bad might happen to whoever talks when the Storyteller has asked for silence."
  },
  {
    "id": "revolutionary",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": ["Used"],
    "setup": False,
    "name": "Revolutionary",
    "team": "fabled",
    "ability": "2 neighboring players are known to be the same alignment. Once per game, one of them registers Falsely."
  },
  {
    "id": "fiddler",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "name": "Fiddler",
    "team": "fabled",
    "ability": "Once per game, the Demon secretly chooses an opposing player: all players choose which of these 2 players win."
  },
  {
    "id": "toymaker",
    "firstNightReminder": "",
    "otherNight": 1,
    "otherNightReminder": "If it is a night when a Demon attack could end the game, and the Demon is marked “Final night: No Attack,” then the Demon does not act tonight. (Do not wake them.)",
    "reminders": ["Final Night: No Attack"],
    "setup": False,
    "name": "Toymaker",
    "team": "fabled",
    "ability": "The Demon may choose not to attack & must do this at least once per game. Evil players get normal starting info."
  },
  {
    "id": "fibbin",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": ["Used"],
    "setup": False,
    "name": "Fibbin",
    "team": "fabled",
    "ability": "Once per game, 1 good player might get False information."
  },
  {
    "id": "duchess",
    "firstNightReminder": "",
    "otherNight": 1,
    "otherNightReminder": "Wake each player marked “Visitor” or “False Info” one at a time. Show them the Duchess token, then fingers (1, 2, 3) equaling the number of evil players marked “Visitor” or, if you are waking the player marked “False Info,” show them any number of fingers except the number of evil players marked “Visitor.”",
    "reminders": ["Visitor", "False Info"],
    "setup": False,
    "name": "Duchess",
    "team": "fabled",
    "ability": "Each day, 3 players may choose to visit you. At night*, each visitor learns how many visitors are evil, but 1 gets False info."
  },
  {
    "id": "sentinel",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": [],
    "setup": True,
    "name": "Sentinel",
    "team": "fabled",
    "ability": "There might be 1 extra or 1 fewer Outsider in play."
  },
  {
    "id": "spiritofivory",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": ["No extra evil"],
    "setup": False,
    "name": "Spirit of Ivory",
    "team": "fabled",
    "ability": "There can't be more than 1 extra evil player."
  },
  {
    "id": "djinn",
    "firstNight": 0,
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": [],
    "setup": False,
    "name": "Djinn",
    "team": "fabled",
    "ability": "Use the Djinn's special rule. All players know what it is."
  },
  {
    "id": "stormcatcher",
    "firstNight": 1,
    "firstNightReminder": "Mark a good player as \"Safe\". Wake each evil player and show them the marked player.",
    "otherNightReminder": "",
    "reminders": ["Safe"],
    "setup": False,
    "name": "Storm Catcher",
    "team": "fabled",
    "ability": "Name a good character. If in play, they can only die by execution, but evil players learn which player it is."
  },
  {
    "id": "deusexfiasco",
    "firstNightReminder": "",
    "otherNightReminder": "",
    "reminders": ["Whoops"],
    "setup": False,
    "name": "Deus ex Fiasco",
    "team": "fabled",
    "ability": "Once per game, the Storyteller will make a \"mistake\", correct it and publicly admit to it."
  }
]
