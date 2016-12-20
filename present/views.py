from present import app

from common import cube, login_required, metrics, s3
from flask import abort, redirect, render_template, request, send_from_directory, session, url_for

import os

@app.errorhandler(cube.CubeError)
def handle_cube_error(error):
    return render_template(
        "error.html",
        error=error)

@app.context_processor
def utility_processor():
    def submit_url_for(puzzle_id):
        return app.config["SUBMIT_URL"] % puzzle_id

    def asset_url_for(asset_path):
      bucket = app.config["AWS_ASSET_BUCKET"]
      if (bucket == 'eastern-toys-assets'):
        return cloudfront_asset_url_for(asset_path)
      return s3.sign(bucket, asset_path, True)

    def cloudfront_asset_url_for(asset_path):
      return s3.cloudfront_sign(asset_path)
    
    def get_google_api_key():
      return app.config["GOOGLE_API_KEY"]
      
    def single_character_unlock_requirement(puzzle_properties):
      sum_constraints = puzzle_properties.get('UnlockedConstraintProperty').get('unlockedConstraint').get('sumConstraints')
      if len(sum_constraints) != 1:
        return {}
      sum_constraint = sum_constraints[0]
      if len(sum_constraint.get('characters')) != 1:
        return {}
      return {'character':sum_constraint.get('characters')[0],'levels':sum_constraint.get('levels')}

    return dict(submit_url_for=submit_url_for, asset_url_for=asset_url_for,
        get_google_api_key=get_google_api_key,
        single_character_unlock_requirement=single_character_unlock_requirement)

CHARACTER_IDS = ['fighter','wizard','cleric','linguist','economist','chemist']
QUEST_IDS = ['dynast','dungeon','thespians','bridge','criminal','minstrels','cube','warlord']

ROUND_PUZZLE_MAP = {
  'index': CHARACTER_IDS + QUEST_IDS + ['rescue_the_linguist','rescue_the_economist','rescue_the_chemist','merchants','fortress'],
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

def make_core_display_data(visibilities_async, team_properties_async):
    visibilities = { v["puzzleId"]: v for v in visibilities_async.result().json().get("visibilities",[]) }
    team_properties = team_properties_async.result().json()
    
    core_display_data = { }
    core_display_data['visible_characters'] = \
        [char_id for char_id in CHARACTER_IDS if visibilities.get(char_id,{}).get('status','INVISIBLE') != 'INVISIBLE']
    core_display_data['solved_characters'] = \
        [char_id for char_id in CHARACTER_IDS if visibilities.get(char_id,{}).get('status','INVISIBLE') == 'SOLVED']
    core_display_data['visible_quests'] = \
        [quest_id for quest_id in QUEST_IDS if visibilities.get(quest_id,{}).get('status','INVISIBLE') != 'INVISIBLE']
    core_display_data['merchants_solved'] = visibilities.get('merchants',{}).get('status','INVISIBLE') == 'SOLVED'
    core_display_data['character_levels'] = { \
        char_id: team_properties.get('teamProperties',{}).get('CharacterLevelsProperty',{}).get('levels',{}).get(char_id.upper(),0) \
        for char_id in core_display_data['visible_characters'] }
    core_display_data['total_character_level'] = sum(core_display_data['character_levels'].itervalues())
    core_display_data['inventory_items'] = team_properties.get('teamProperties',{}).get('InventoryProperty',{}).get('inventoryItems',[])
    core_display_data['gold'] = team_properties.get('teamProperties',{}).get('GoldProperty',{}).get('gold',0)
    return core_display_data
    
def get_full_path_core_display_data():
    core_display_data = { }
    core_display_data['visible_characters'] = CHARACTER_IDS
    core_display_data['visible_quests'] = QUEST_IDS
    core_display_data['merchants_solved'] = False
    core_display_data['character_levels'] = { char_id: 0 for char_id in core_display_data['visible_characters'] }
    core_display_data['total_character_level'] = sum(core_display_data['character_levels'].itervalues())
    core_display_data['inventory_items'] = ['ITEM' + str(i) for i in range(14,24)]
    core_display_data['gold'] = 0
    return core_display_data

@app.route("/")
@login_required.solvingteam
@metrics.time("present.index")
def index():
    round_puzzle_ids = ROUND_PUZZLE_MAP.get('index')

    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + ['merchants'])
    core_team_properties_async = cube.get_team_properties_async(app)
    puzzle_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, round_puzzle_ids)
    puzzle_properties_async = cube.get_all_puzzle_properties_for_list_async(app, round_puzzle_ids)
    
    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    puzzle_visibilities = { v["puzzleId"]: v for v in puzzle_visibilities_async.result().json().get("visibilities",[]) }
    puzzle_properties = {puzzle.get('puzzleId'): puzzle for puzzle in puzzle_properties_async.result().json().get('puzzles',[])}
    visible_puzzle_ids = set([key for key in puzzle_visibilities if puzzle_visibilities.get(key,{}).get('status','') != 'INVISIBLE'])
    fog_number = len([map_item for map_item in \
        ['dynast','dungeon','thespians','bridge','criminal','minstrels','cube','warlord','rescue_the_linguist','rescue_the_chemist','rescue_the_economist','merchants','fortress']\
        if map_item in visible_puzzle_ids])

    with metrics.timer("present.index_render"):
        return render_template(
            "index.html",
            core_display_data=core_display_data,
            visible_puzzle_ids=visible_puzzle_ids,
            fog_number=fog_number,
            puzzle_visibilities=puzzle_visibilities)

@app.route("/round/<round_id>")
@login_required.solvingteam
@metrics.time("present.round")
def round(round_id):
    round_puzzle_ids = ROUND_PUZZLE_MAP.get(round_id,[])
    round_puzzle_ids.append(round_id)

    round_visibility_async = cube.get_puzzle_visibility_async(app, round_id)
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + ['merchants'])
    core_team_properties_async = cube.get_team_properties_async(app)
    puzzle_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, round_puzzle_ids)
    puzzle_properties_async = cube.get_all_puzzle_properties_for_list_async(app, round_puzzle_ids)
    
    round_visibility = round_visibility_async.result().json()
    if round_visibility['status'] not in ['UNLOCKED','SOLVED']:
        abort(403)
    
    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    puzzle_visibilities = { v["puzzleId"]: v for v in puzzle_visibilities_async.result().json().get("visibilities",[]) }
    puzzle_properties = {puzzle.get('puzzleId'): puzzle for puzzle in puzzle_properties_async.result().json().get('puzzles',[])}

    with metrics.timer("present.round_render"):
        return render_template(
            "rounds/%s.html" % round_id,
            core_display_data=core_display_data,
            round_id=round_id,
            puzzle_properties=puzzle_properties,
            puzzle_visibilities=puzzle_visibilities)


@app.route("/puzzle/<puzzle_id>")
@login_required.solvingteam
@metrics.time("present.puzzle")
def puzzle(puzzle_id):
    puzzle_visibility_async = cube.get_puzzle_visibility_async(app, puzzle_id)
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + ['merchants'])
    core_team_properties_async = cube.get_team_properties_async(app)
    puzzle_async = cube.get_puzzle_async(app, puzzle_id)

    puzzle_visibility = puzzle_visibility_async.result().json()
    if puzzle_visibility['status'] not in ['UNLOCKED','SOLVED']:
        abort(403)

    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    puzzle = puzzle_async.result().json()
    canonical_puzzle_id = puzzle.get('puzzleId')
    puzzle_round_id = [r_id for r_id, round_puzzle_ids in ROUND_PUZZLE_MAP.iteritems() if canonical_puzzle_id in round_puzzle_ids]
    puzzle_round_id = puzzle_round_id[0] if len(puzzle_round_id) > 0 else None

    with metrics.timer("present.puzzle_render"):
        return render_template(
            "puzzles/%s.html" % puzzle_id,
            core_display_data=core_display_data,
            puzzle_id=puzzle_id,
            puzzle_round_id=puzzle_round_id,
            puzzle=puzzle,
            puzzle_visibility=puzzle_visibility)

@app.route("/inventory")
@login_required.solvingteam
def inventory():
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + ['merchants'])
    core_team_properties_async = cube.get_team_properties_async(app)

    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    return render_template("inventory.html", core_display_data=core_display_data)

@app.route("/full/puzzle")
@login_required.writingteam
def full_puzzle_index():
    files = os.listdir(os.path.join(app.root_path, 'templates/puzzles'))
    puzzle_ids = [file.split('.')[0] for file in files]
    puzzle_ids = sorted([puzzle_id for puzzle_id in puzzle_ids if puzzle_id not in ['puzzle_layout','sample_draft']])
    core_display_data = get_full_path_core_display_data()
    return render_template("full_puzzle_index.html",
        core_display_data=core_display_data,
        puzzle_ids=puzzle_ids)
        
@app.route("/full/puzzle/<puzzle_id>")
@login_required.writingteam
def full_puzzle(puzzle_id):
    try:
        puzzle = cube.get_puzzle(app, puzzle_id)
        canonical_puzzle_id = puzzle.get('puzzleId')
        puzzle_round_id = [r_id for r_id, round_puzzle_ids in ROUND_PUZZLE_MAP.iteritems() if canonical_puzzle_id in round_puzzle_ids]
        puzzle_round_id = puzzle_round_id[0] if len(puzzle_round_id) > 0 else None
    except:
        puzzle = None
        puzzle_round_id = None
    core_display_data = get_full_path_core_display_data()
    return render_template(
        "puzzles/%s.html" % puzzle_id,
        core_display_data=core_display_data,
        puzzle_id=puzzle_id,
        puzzle_round_id=puzzle_round_id,
        puzzle=puzzle)

@app.route("/full/solution/<puzzle_id>")
@login_required.writingteam
def full_solution(puzzle_id):
    core_display_data = get_full_path_core_display_data()
    return render_template(
        "solutions/%s.html" % puzzle_id,
        core_display_data=core_display_data,
        puzzle_id=puzzle_id)

@app.route("/full/round/<round_id>")
@login_required.writingteam
def full_round(round_id):
    puzzle_properties = cube.get_puzzles(app)
    puzzle_properties = {puzzle.get('puzzleId'): puzzle for puzzle in puzzle_properties}
    
    core_display_data = get_full_path_core_display_data()
    visibility = request.args.get('visibility','VISIBLE')
    puzzle_visibilities = {puzzle_id: {'status': visibility} for puzzle_id in puzzle_properties.keys()}
    
    return render_template(
        "rounds/%s.html" % round_id,
        core_display_data=core_display_data,
        round_id=round_id,
        puzzle_properties=puzzle_properties,
        puzzle_visibilities=puzzle_visibilities,
        full_access = True)

@app.route("/full/inventory")
@login_required.writingteam
def full_inventory():
    core_display_data = get_full_path_core_display_data()
    return render_template("inventory.html",
        core_display_data=core_display_data)

