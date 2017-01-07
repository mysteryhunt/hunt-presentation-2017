from present import app

from flask import request
from cryptography.fernet import Fernet
from werkzeug.contrib.cache import SimpleCache

import string
import json
import numpy as np
import random
import os
import re

## CRACKPOT OR SNACKPOT

#More puzzle-ish stuff

#### I don't know how to parse HTML properly, but here's
#### a way to grab titles and (unparsed) author-strings from a vixra HTML scrape.
def get_vixradb():
  vixradb = {} # use a dict

  with open(os.path.join(os.path.dirname(app.root_path), "vixra_dumps.htm")) as file:
    while (True):
      line = file.readline()
      if len(line) == 0:
        break
      if "<h3>" in line: #it's a new title.  Get the title
        titlegrep = re.compile("<h3>(.+?)</h3>")
        vtitle = titlegrep.search(line).group(1)
        file.readline() #then skip a line
        authorline = file.readline().strip() + file.readline().strip() #then get the author list on two lines
        authorgrep = re.compile("<p>(.+?)</p>")
        vauthors = authorgrep.search(authorline).group(1)
        vixradb[vtitle] = vauthors
  return vixradb

vixradb = get_vixradb()

pre = set(("on","of","through","towards","for","with","to","from","by","in","that","between","as"))
con = set(("and","or"))
art = set(("the","a","its","not"))
adj = set(("thermal","transformative","big","small","electromagnetic","brown","never","gaseous","motionless","combustible","interstellar","polarizable","fundamental","new","kirchhoffs","Earths","magnetic","gravitational","bulk","young","hypothetical","venusian","fermats","boys","last","may","not","new","three","planetary","further","away","dark","observable","electrochemically","nuclear","stellar","luminous","dark","hypothetical","grand","fifth","fundamental","proposed","ballistic","light","future","induced","gev","milroy","grand","ballistic","proposed","possible","left-right"))
ver = set(("happened","field","form","design","provides","be","is","process","proposed","test","induced","determine","why","approach"))
ger = set(("transgressing","eliminating","engineering","getting"))
nou = set(("bang","boundaries","quantum","brown","chance","design","device","electro-gravity","electrodynamics","engineering","emission","explanation","field","flight","form","generator","gravity","hermeneutics","inference","law","o(3)","probabilities","townsend","vacuum","validity","water","zero-point","fundamental","basis","mechanics","possibility","shielding","bulk","superconductor","YBa2Cu207-x","energy","confirmation","age","biofield","signals","transmission","neutrinos","process","physics","information","theory","quantum","space","matter","snake","object","fauna","quiton/perceptron","existence","perception","phenomena","theorem","hanson","grammar","school","proof","hole","escape","velocity","case","study","decay","experiment","data","quantum","entanglement","laws","motion","rate","earth","sun","process","physics","information","theory","space","matter","cobe","wmap","signal","analysis","fact","fiction","dark","matter","observable","oscillations","fusion","deuterium","astrophysics","connections","ignition","matter","axion","rockets","terms","energy","flow","wire","milroy","engine","concept","bio-force","force","fundamental","test","theory","emission","light","particles","energy","lithium","entropy","neutrino","physics","problem","stars","matter-antimatter","gamma","ray","laser","rocket","propulsion","flow","wire","engine","unification","concept","test","theory","answer","asymmetry","beta","decay","airfoil","approach","propulsion"))
postfix = set(("why",))



# these are utterly bogus heuristics for making some titles more intelligible
def punctuate(title): # argument is title as split string
    tl = len(title)
    if (title[-1] == 'Why'):
        title[-1] = 'Why?'        
        title[-2] = title[-2]+":"

    for i in range(1,tl): # look for things of the form
        if (title[i] == 'The' or title[i] == 'A'):
            if (title[i-1].lower() not in pre | con | ver | ger):
                title[i-1] = title[i-1]+":"
            
        
    return " ".join(title) # return value is concatenated title


def checkgrammar(title):
    tl = len(title)
    for i in range(tl-1):
        # check that prepositions precede nouns, articles, gerunds, or adjectives
        if (title[i] in pre and (title[i+1] not in art and title[i+1] not in adj and title[i+1] not in nou and title[i+1] not in ger)):
            return False       
        
        # check that adjectives precede nouns or article-noun pairs
        if (title[i] in adj and title[i+1] not in nou and title[i+1] not in con):
            return False       
            
        #check that articles preced nouns, adjectives
        if (title[i] in art and title[i+1] not in nou and title[i+1] not in adj):
            return False
   
    for i in range(1,tl-2):
        #check that conjunctions are preceded and followed by the same thing
        if (title[i] in con and not ((title[i-1] in ger and title[i+1] in ger) or 
            (title[i-1] in adj and title[i+1] in adj) or 
            (title[i-1] in nou and title[i+1] in nou) or
            (title[i-1] in pre and title[i+1] in pre))
            ):
            return False
    # check that final word is a noun or verb or a postfixable
    if (title[tl-1] not in nou and title[tl-1] not in ver and title[tl-1] not in adj and title[tl-1] not in postfix):
        return False
    return True


#### hand-code heuristics here to try to make the fake titles look better
#### will need tweaking and some grammar when the final-ish clueset is in place
def exclude(x):
    xs = x.split()
    articles = ("the","a")
    prepositions = ("with","on","of","in","for")
    nouns = ("dark","matter","planets","comets","paradoxes","origins")
    
    if any(xs[0]==oof for oof in ("happened","resolved","with")):
        return True
    if any(xs[-1]==oof for oof in ("the","and","on","a","of","in","with","for","Symmes\'")):
        return True
    if any(oof in x for oof in ("the of","the a","new the","of on","on of","the for","an a", "a of" ,"the the","on of","of in","in of","of of","the in","of and","in and","of for","a the")):
        return True
    if any(oof in x for oof in ["an "+char for char in "bcdfghjklmnpqrstvwxyz"]):
        return True
    if any(oof in x for oof in ["a "+char for char in "aeiou"]):
        return True

    if any(oof in x for oof in ["symmes' "+word for word in ("in","the","and")]):
        return True        
    return False

#### Here is the set of eight famous-ish crackpot paper titles whose words will be used for fake-title generation.
titleset = [
    'Electrochemically induced nuclear fusion of deuterium',
    'Questioning Astrophysics and Revealing Connections Between Stellar Ignition Luminous',
    'Airfoil Force Approach to the Rocket Propulsion',
    'Electromagnetic Energy Flow in the Wire and Milroy Engine',
    'Grand Unification Concept with Bio-force as the Fifth Fundamental',
    'A proposed astronomical test of the ballistic theory of',
    'A Possible Answer to the Right-Left Asymmetry of Beta Decay',
    'Entropy Neutrino Physics and the Lithium Problem Why Stars']
titleset = [x.lower().split() for x in titleset] # clean it up a little
authorset = [["Pons","Fleischmann"],["Herndon",],["Jovanovich",],["Khmelnik",],["Kodukula",],["Dingle",],["Yie",],["Beckwith",]]

#one word from each title will go unused.  we'll clue them later and they will read off the answer.
#counting from 1=first word
readoutset = [4,8,6,9,4,7,3,6]    


# This function will parse a real paper title and try to convert it into a "vixra number" following the
# puzzle convention.  It'll raise NameError if it thinks we ought not to use this title.
def strict_title_to_number(stitle):
  title = stitle.lower().split()
  if (len(title) > 8): # ignore vixra articles with long titles
    raise NameError("toolong")
  if (len(title) < 5): #ignore vixra articles with short titles
    raise NameError("tooshort")
  thisid = ['0']*8     #by default the identifier is 0000.0000 except where we find matches
  offset = 0 # how many spaces have we inserted
  maxoffset = 8 - len(title)
  n=0
  for iid in range(maxoffset,8):
    nthword = "DUMMYVARIABLE"
    if (n < len(title)):
      nthword = title[n]
    if nthword in titleset[iid]:
      thisid[iid] = str(titleset[iid].index(nthword) + 1)
      n +=1
    else:
      thisid[iid] = '0' # we're just filling out with 'i's
      n += 1
      # uncomment this next bit if you want to only use vixra titles with a nonzero number of matches
#    if all(i is '0' for i in thisid):  
#        return NameError("nohits")
  return "".join(thisid[0:4])+"."+"".join(thisid[4:8])
    
### this function generates fake paper titles with words drawn from the clueset.
def goodtitle(minwords=4):
    xtitleset = [["",]+title for title in titleset] # add a "blank" to allow zero to be drawn
    tlens = [len(title) for title in xtitleset]
    while (True):
        titlechoice = [np.random.randint(1,min(10,number)) for number in tlens] #pick random word from each title
        if (minwords < 8):
            titlelen = np.random.randint(minwords,8) # how many words to use?
            for putzerohere in random.sample(range(8),8-titlelen): #choose which words to leave blank
                titlechoice[putzerohere] = 0
        if any( [readoutset[i]==titlechoice[i] for i in range(8)] ): # skip it if we've drawn a "readout" word 
            continue 
        faketitle = " ".join([xtitleset[i][titlechoice[i]] for i in range(8)])
        faketitle = " ".join(faketitle.split()) #clean up extra spaces
        if not checkgrammar(faketitle.split()):  #skip it if if violates one of our grammar heuristics
            continue
        faketitle = faketitle.title() # use title case
        faketitle = punctuate(faketitle.split())
    
        faketitle = faketitle.replace("Kirchhoffs","Kirchhoff's") # fix apostrophe in Kirchoff's
        faketitle = faketitle.replace("Earths","Earth's") # fix apostrophe in Kirchoff's
        faketitle = faketitle.replace("Cobe","COBE") # fix apostrophe in Kirchoff's
        faketitle = faketitle.replace("Wmap","WMAP") # fix apostrophe in Kirchoff's
        faketitle = faketitle.replace("Fermats","Fermat's") # fix apostrophe in Kirchoff's
        faketitle = faketitle.replace("Boys","Boys'") # fix apostrophe in Kirchoff's
        faketitle = faketitle.replace("Gev","GeV") # fix apostrophe in Kirchoff's

        return ("".join([str(d) for d in titlechoice[0:4]])+"."+"".join([str(d) for d in titlechoice[4:8]]), faketitle) # return the fake vixra ID and the fake title, in title case

def getauthorlist(idstring):
    alist1 = [authorset[i] for i, val in enumerate(idstring[0:4]+ idstring[5:9]) if (int(val) != 0)]
    aset = [a for xset in alist1 for a in xset]
    saset = sorted(aset)
    astring = ", ".join(saset[:-1]) + ", and " + saset[-1]
    return astring



#More server-related stuff

cache = SimpleCache()
key = '1rVm3Kgtn3prMeCZLyQn8BroT2NwomVU-iWdVnzd_pA='
cipher_suite = Fernet(key)

def generate_salt(size=6, chars=string.ascii_uppercase + string.digits):
  return ''.join(random.choice(chars) for _ in range(size))

def encrypt_tuple(tuple):
  return cipher_suite.encrypt('|'.join(tuple))
  
def encrypt_dict(d):
  return encrypt_tuple((generate_salt(), json.dumps(d)))

def decrypt_tuple(token):
  b = token.encode('utf-16be')
  return tuple(cipher_suite.decrypt(b).split('|'))
  
def decrypt_dict(token):
  return json.loads(decrypt_tuple(token)[1])
  
def make_real():
  while (True):  # while loop until one finds a parseable vixra title
    try:        
      realtitle = random.choice(vixradb.keys())
      realid = strict_title_to_number(realtitle)
    except NameError:
      continue
    break
  return {
    'title': realtitle,
    'archive': 'vixra',
    'archive_id': realid
  }
  
def make_fake():
  created = goodtitle()
  return {
    'title': created[1],
    'archive': 'snixra',
    'archive_id': created[0],
    'authors': getauthorlist(created[0])
  }

HINTS = [
  "You must be new at this.<br/>SniXra recommends reading AIP conference paper ????.????",
  "Maybe the ivory tower will cut you some slack.<br/>SniXra recommends reading AIP conference paper ????.???6",
  "You're still a longshot, but so is mainstream science.<br/>SniXra recommends reading AIP conference paper ?8??.???6",
  "Your geocities page has a very professional sheen.<br/>SniXra recommends reading AIP conference paper ?8??.?7?6",
  "You have the big picture, someone else will do the math, right?<br/>SniXra recommends reading AIP conference paper 48??.?7?6",
  "Your physics manifesto is propping up a table leg in a real department coffee room.<br/>SniXra recommends reading AIP conference paper 48??.?736",
  "You should name your theory after yourself.<br/>SniXra recommends reading AIP conference paper 48?9.?736",
  "An outsider like you can recognize epicycles as epicycles.<br/>SniXra recommends reading AIP conference paper 48?9.4736",
  "You were right. Einstein was wrong.<br/>SniXra recommends reading AIP conference paper 4869.4736",
  ]
  
def make_hint(correct, total):
  return HINTS[min(8,min(total-1,int(correct*1.0/total*9)))]
  
@app.route('/crackpot_or_snackpot/problem')
def problem():
  real = make_real()
  fake = make_fake()
  resp = {}
  if (np.random.randint(2)+1 == 1):
    resp['left'] = real['title']
    resp['right'] = fake['title']
    correct = 'L'
  else:
    resp['left'] = fake['title']
    resp['right'] = real['title']
    correct = 'R'
  problem_spec = {
    'real': real,
    'fake': fake,
    'correct': correct
  }
  problem_spec = encrypt_dict(problem_spec)
  resp['problem_token'] = problem_spec
  
  return json.dumps(resp)

@app.route('/crackpot_or_snackpot/solution')
def solution():
  problem_spec = request.args.get('problem_token')
  if problem_spec is None:
    return json.dumps({'message':'Must provide problem token'})
  cached = cache.get(problem_spec)
  if cached is not None:
    return json.dumps({'message':'This token has already been answered'})
  cache.set(problem_spec, 1, timeout=5*60)
  
  given_answer = request.args.get('answer')
  if given_answer is None:
    return json.dumps({'message':'Must provide answer'})
    
  state_token = request.args.get('state_token')
  if state_token is None:
    state = {
      'correct': 0,
      'total': 0
    }
  else:
    state = decrypt_dict(state_token)
    
  problem = decrypt_dict(problem_spec)

  resp = {
    'user_answer': given_answer,
    'correct_answer': problem['correct']
  }
  resp['fake'] = problem['fake']
  if problem['correct'] == 'L':
    resp['left'] = problem['real']
    resp['right'] = problem['fake']
  else:
    resp['left'] = problem['fake']
    resp['right'] = problem['real']
  
  state['total'] += 1
  if problem['correct'] == given_answer:
    state['correct'] += 1
    resp['this_answer_correct'] = 1
  else:
    resp['this_answer_correct'] = 0
  resp['hint'] = make_hint(state['correct'], state['total'])
  resp['state'] = state
  resp['state_token'] = encrypt_dict(state)

  return json.dumps(resp)