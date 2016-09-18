#FIGHTER

fighter_round = {
  'id': 'fighter',
  'puzzles': ['f1', 'f2', 'f3']
}

fighter_class = {
  'class_identifier': 'FIGHTER',
  'round': fighter_round
}


#WIZARD

wizard_round = {
  'id': 'wizard',
  'puzzles': ['w1','w2','w3']
}

wizard_class = {
  'class_identifier': 'WIZARD',
  'round': wizard_round
}


#CLERIC

cleric_round = {
  'id': 'cleric',
  'puzzles': ['cl1','cl2','cl3']
}

cleric_class = {
  'class_identifier': 'CLERIC',
  'round': cleric_round
}

#LINGUIST

linguist_round = {
  'id': 'linguist',
  'puzzles': []
}

linguist_class = {
  'class_identifier': 'LINGUIST',
  'round': linguist_round
}

#CHEMIST

chemist_round = {
  'id': 'chemist',
  'puzzles': []
}

chemist_class = {
  'class_identifier': 'CHEMIST',
  'round': chemist_round
}

#ECONOMIST

economist_round = {
  'id': 'economist',
  'puzzles': []  
}

economist_class = {
  'class_identifier': 'ECONOMIST',
  'round': economist_round
}

PUZZLES = {
  'character_classes': [fighter_class, wizard_class, cleric_class, linguist_class, chemist_class, economist_class],
  'rounds': {
    'fighter': fighter_round,
    'wizard': wizard_round,
    'cleric': cleric_round,
    'linguist': linguist_round,
    'chemist': chemist_round,
    'economist': economist_round
  }
}