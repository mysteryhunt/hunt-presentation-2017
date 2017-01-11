from present import app

from common import cube, login_required, metrics, s3
from common.round_puzzle_map import CHARACTER_IDS, QUEST_IDS, ROUND_PUZZLE_MAP
from flask import abort, redirect, render_template, request, send_from_directory, session, url_for
import pyformance
from requests.exceptions import RequestException

import os
import re

@app.errorhandler(Exception)
def handle_exception(error):
    error_string = str(error)
    if isinstance(error, RequestException) and error.response is not None:
        pyformance.global_registry().counter("present.error.%d" % error.response.status_code).inc()
        error_string += ": %s" % error.response.json()
    else:
        pyformance.global_registry().counter("present.error.500").inc()
    return render_template(
        "error.html",
        error=error_string)

@app.errorhandler(403)
def handle_forbidden(error):
    pyformance.global_registry().counter("present.error.403").inc()
    return render_template(
        "error.html",
        error=error)

@app.errorhandler(404)
def handle_not_found(error):
    pyformance.global_registry().counter("present.error.404").inc()
    return render_template(
        "error.html",
        error=error)

@app.errorhandler(500)
def handle_internal_server_error(error):
    pyformance.global_registry().counter("present.error.500").inc()
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
    
    def pretty_title(title):
      title = re.sub('(_+)','<span class="answer-blank">\\1</span>',title)
      title = re.sub("'", "&rsquo;",title) #Assumes there are no enclosed single quotes, i.e., all of these are apostrophes
      title = re.sub('^\\.\\.\\.', '.&nbsp;.&nbsp;.&nbsp;',title)
      title = re.sub('\\.\\.\\.', '&nbsp;.&nbsp;.&nbsp;.',title)
      return title
    
    def site_mode():
      return app.config["SITE_MODE"] if app.config["SITE_MODE"] else 'live'
      
    def pretty_truncate(value, length):
      if len(value) <= length:
        return value
      return value[0:length] + '...'

    return dict(submit_url_for=submit_url_for, asset_url_for=asset_url_for,
        get_google_api_key=get_google_api_key,
        single_character_unlock_requirement=single_character_unlock_requirement,
        pretty_title=pretty_title,
        site_mode=site_mode,
        pretty_truncate=pretty_truncate)

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
    core_display_data['battle_solved'] = visibilities.get('battle',{}).get('status','INVISIBLE') == 'SOLVED'
    core_display_data['character_levels'] = { \
        char_id: team_properties.get('teamProperties',{}).get('CharacterLevelsProperty',{}).get('levels',{}).get(char_id.upper(),0) \
        for char_id in core_display_data['visible_characters'] }
    core_display_data['total_character_level'] = sum(core_display_data['character_levels'].itervalues())
    core_display_data['inventory_items'] = team_properties.get('teamProperties',{}).get('InventoryProperty',{}).get('inventoryItems',[])
    core_display_data['gold'] = team_properties.get('teamProperties',{}).get('GoldProperty',{}).get('gold',0)
    core_display_data['email'] = team_properties.get('email','')
    core_display_data['primaryPhone'] = team_properties.get('primaryPhone','')
    core_display_data['secondaryPhone'] = team_properties.get('secondaryPhone','')
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
    core_display_data['email'] = ''
    core_display_data['primaryPhone'] = ''
    core_display_data['secondaryPhone'] = ''
    return core_display_data

@app.route("/")
@login_required.solvingteam
@metrics.time("present.index")
def index():
    if not cube.is_hunt_started_async(app).result():
        return prehunt_index();
    round_puzzle_ids = ROUND_PUZZLE_MAP.get('index')

    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
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

def prehunt_index():
    return render_template("prehunt_index.html")

@app.route("/round/<round_id>")
@login_required.solvingteam
@metrics.time("present.round")
def round(round_id):
    round_puzzle_ids = ROUND_PUZZLE_MAP.get(round_id,[]) + [round_id]

    round_visibility_async = cube.get_puzzle_visibility_async(app, round_id)
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
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
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
    core_team_properties_async = cube.get_team_properties_async(app)
    puzzle_async = cube.get_puzzle_async(app, puzzle_id)

    puzzle_visibility = puzzle_visibility_async.result().json()
    if puzzle_id != 'fortress' and puzzle_visibility['status'] not in ['UNLOCKED','SOLVED']:
        abort(403)
    if puzzle_id == 'fortress' and puzzle_visibility['status'] not in ['VISIBLE','UNLOCKED','SOLVED']:
        abort(403)
        
    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    puzzle = puzzle_async.result().json()
    canonical_puzzle_id = puzzle.get('puzzleId')
    puzzle_round_id = [r_id for r_id, round_puzzle_ids in ROUND_PUZZLE_MAP.iteritems() if canonical_puzzle_id in round_puzzle_ids]
    puzzle_round_id = puzzle_round_id[0] if len(puzzle_round_id) > 0 else None

    if puzzle_id == 'fortress' and puzzle_visibility['status'] in ['VISIBLE']:
      with metrics.timer("present.puzzle_render"):
          return render_template(
              "puzzles/fortress_locked.html",
              core_display_data=core_display_data,
              puzzle_id=puzzle_id,
              puzzle_round_id=puzzle_round_id,
              puzzle=puzzle,
              puzzle_visibility=puzzle_visibility)

    with metrics.timer("present.puzzle_render"):
        return render_template(
            "puzzles/%s.html" % puzzle_id,
            core_display_data=core_display_data,
            puzzle_id=puzzle_id,
            puzzle_round_id=puzzle_round_id,
            puzzle=puzzle,
            puzzle_visibility=puzzle_visibility)

            
@app.route("/solution/<puzzle_id>")
@login_required.solvingteam
@metrics.time("present.solution")
def puzzle_solution(puzzle_id):
    if app.config["SITE_MODE"] != 'solution':
        abort(403)
    
    puzzle_visibility_async = cube.get_puzzle_visibility_async(app, puzzle_id)
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
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
            "solutions/%s.html" % puzzle_id,
            core_display_data=core_display_data,
            puzzle_id=puzzle_id,
            puzzle_round_id=puzzle_round_id,
            puzzle=puzzle,
            puzzle_visibility=puzzle_visibility)

@app.route("/puzzle")
@login_required.solvingteam
@metrics.time("present.puzzle_list")
def puzzle_list():
    if not cube.is_hunt_started_async(app).result():
        abort(403);
  
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
    core_team_properties_async = cube.get_team_properties_async(app)
    all_visibilities_async = cube.get_puzzle_visibilities_async(app)
    all_puzzles_async = cube.get_all_puzzle_properties_async(app)

    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    all_visibilities = { v["puzzleId"]: v for v in all_visibilities_async.result().json()["visibilities"] }
    all_puzzles = { v["puzzleId"]: v for v in all_puzzles_async.result().json()["puzzles"] }

    with metrics.timer("present.puzzle_list_render"):
        return render_template(
            "puzzle_list.html",
            core_display_data=core_display_data,
            all_visibilities=all_visibilities,
            all_puzzles=all_puzzles,
            round_puzzle_map=ROUND_PUZZLE_MAP)

@app.route("/inventory")
@login_required.solvingteam
def inventory():
    if not cube.is_hunt_started_async(app).result():
        abort(403);
  
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
    core_team_properties_async = cube.get_team_properties_async(app)

    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
    return render_template("inventory.html", core_display_data=core_display_data)

@app.route("/handbook")
@login_required.solvingteam
def handbook():
    is_hunt_started_async = cube.is_hunt_started_async(app)
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
    core_team_properties_async = cube.get_team_properties_async(app)

    if is_hunt_started_async.result():
        core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
        return render_template("handbook.html", core_display_data=core_display_data)
    else:
        return render_template("handbook.html")

@app.route("/safety")
@login_required.solvingteam
def safety():
    is_hunt_started_async = cube.is_hunt_started_async(app)
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
    core_team_properties_async = cube.get_team_properties_async(app)

    if is_hunt_started_async.result():
        core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)
        return render_template("safety.html", core_display_data=core_display_data)
    else:
        return render_template("safety.html")

@app.route("/change_contact_info", methods=["POST"])
@login_required.solvingteam
def change_contact_info():
    cube.update_team(app, session["username"], {
        "teamId": session["username"],
        "email": request.form["email"],
        "primaryPhone": request.form["primaryPhone"],
        "secondaryPhone": request.form["secondaryPhone"],
    })
    if request.referrer:
        return redirect(request.referrer)
    return redirect(url_for("index"))

@app.route("/activity_log")
@login_required.solvingteam
@metrics.time("present.activity_log")
def activity_log():
    core_visibilities_async = cube.get_puzzle_visibilities_for_list_async(app, CHARACTER_IDS + QUEST_IDS + ['merchants','battle'])
    core_team_properties_async = cube.get_team_properties_async(app)
    team_visibility_changes_async = cube.get_team_visibility_changes_async(app)
    team_submissions_async = cube.get_team_submissions_async(app)
    all_puzzles_async = cube.get_all_puzzle_properties_async(app)

    core_display_data = make_core_display_data(core_visibilities_async, core_team_properties_async)

    visibility_changes = [vc for vc in team_visibility_changes_async.result()
                          if vc["status"] in ['UNLOCKED', 'SOLVED'] and not vc["puzzleId"].startswith("event")]
    activity_entries = visibility_changes + team_submissions_async.result()
    activity_entries.sort(key=lambda entry: entry["timestamp"], reverse=True)

    all_puzzles = { v["puzzleId"]: v for v in all_puzzles_async.result().json()["puzzles"] }

    return render_template(
        "activity_log.html",
        core_display_data=core_display_data,
        activity_entries=activity_entries,
        all_puzzles=all_puzzles)

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



