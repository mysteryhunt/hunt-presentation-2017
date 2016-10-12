from present import app

from common import cube, login_required, s3
from flask import redirect, render_template, request, send_from_directory, session, url_for

import os

@app.context_processor
def utility_processor():
    def submit_url_for(puzzle_id):
        return app.config["SUBMIT_URL"] % puzzle_id

    def asset_url_for(asset_path):
      bucket = app.config["AWS_ASSET_BUCKET"]
      access_key = app.config["AWS_ASSET_ACCESS_KEY"]
      secret_key = app.config["AWS_ASSET_SECRET_KEY"]
      return s3.sign(bucket, asset_path, access_key, secret_key, True)
    
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

    def single_character_reward(puzzle_properties):
      character_reward = puzzle_properties.get('SolveRewardProperty').get('characterLevels')
      character_reward = [{'character': k, 'levels': v} for k,v in character_reward.iteritems()]
      if len(character_reward) != 1:
        return {}
      return character_reward[0]

    return dict(submit_url_for=submit_url_for, asset_url_for=asset_url_for,
        get_google_api_key=get_google_api_key,
        single_character_unlock_requirement=single_character_unlock_requirement,
        single_character_reward=single_character_reward)
    


@app.route("/")
@login_required.solvingteam
def index():
    visible_puzzle_ids = set(cube.get_visible_puzzle_ids(app))
    team_properties = cube.get_team_properties(app)
    return render_template("index.html", visible_puzzle_ids=visible_puzzle_ids, team_properties=team_properties)

@app.route("/round/<round_id>")
@login_required.solvingteam
def round(round_id):
    if not cube.is_puzzle_unlocked(app, round_id):
        abort(403)

    puzzle_properties = cube.get_all_puzzle_properties(app)
    puzzle_properties = {puzzle.get('puzzleId'): puzzle for puzzle in puzzle_properties.get('puzzles',[])}
    puzzle_visibilities = cube.get_puzzle_visibilities(app)
    puzzle_visibilities = {visibility.get('puzzleId'): visibility for visibility in puzzle_visibilities}
    team_properties = cube.get_team_properties(app)
    
    return render_template(
        "rounds/%s.html" % round_id,
        round_id=round_id,
        puzzle_properties=puzzle_properties,
        puzzle_visibilities=puzzle_visibilities,
        team_properties=team_properties)


@app.route("/puzzle/<puzzle_id>")
@login_required.solvingteam
def puzzle(puzzle_id):
    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    return render_template(
        "puzzles/%s.html" % puzzle_id,
        puzzle_id=puzzle_id)

@app.route("/full/puzzle")
@login_required.writingteam
def full_puzzle_index():
    files = os.listdir(os.path.join(app.root_path, 'templates/puzzles'))
    puzzle_ids = [file.split('.')[0] for file in files]
    puzzle_ids = [puzzle_id for puzzle_id in puzzle_ids if puzzle_id not in ['puzzle_layout','sample_draft']]
    return render_template("full_puzzle_index.html", puzzle_ids=puzzle_ids)
        
@app.route("/full/puzzle/<puzzle_id>")
@login_required.writingteam
def full_puzzle(puzzle_id):
    return render_template(
        "puzzles/%s.html" % puzzle_id,
        puzzle_id=puzzle_id)

@app.route("/full/solution/<puzzle_id>")
@login_required.writingteam
def full_solution(puzzle_id):
    return render_template(
        "solutions/%s.html" % puzzle_id,
        puzzle_id=puzzle_id)
