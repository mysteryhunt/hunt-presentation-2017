CHARACTER_IDS = ['fighter','wizard','cleric','linguist','economist','chemist']
QUEST_IDS = ['dynast','dungeon','thespians','bridge','criminal','minstrels','cube','warlord']

ROUND_PUZZLE_MAP = {
  'index': CHARACTER_IDS + QUEST_IDS + ['rescue_the_linguist','rescue_the_economist','rescue_the_chemist','merchants','encounter','fortress'],
  'fighter': ['f' + str(i) for i in range(1,11+1)],
  'wizard': ['w' + str(i) for i in range(1,11+1)],
  'cleric': ['cl-l' + str(i) for i in range(1,5+1)] + ['cl-r' + str(i) for i in range(1,5+1)],
  'linguist': ['l' + str(i) for i in range(1,12+1)],
  'economist': ['e' + str(i) for i in range(1,8+1)],
  'chemist': ['ch' + str(i) for i in range(1,9+1)],
  'dynast': ['dynast' + str(i) for i in range(1,11+1)],
  'dungeon': ['dungeon' + str(i) for i in range(1,11+1)],
  'thespians': ['thespians-l' + str(i) for i in range(1,5+1)] + ['thespians-r' + str(i) for i in range(1,5+1)],
  'bridge': ['bridge' + str(i) for i in range(1,16+1)],
  'criminal': ['criminal' + str(i) for i in range(1,10+1)],
  'minstrels': ['minstrels' + str(i) for i in range(1,7+1)],
  'cube': ['cube' + str(i) for i in range(1,8+1)],
  'warlord': ['warlord-' + direction for direction in ['nw','nc','ne','cw','cc','ce','sw','sc','se']]
}
