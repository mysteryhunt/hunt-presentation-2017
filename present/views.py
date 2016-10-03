from present import app

from common import cube, s3
from flask import redirect, render_template, request, send_from_directory, session, url_for

@app.context_processor
def utility_processor():
    def submit_url_for(puzzle_id):
        return app.config["SUBMIT_URL"] % puzzle_id

    def asset_url_for(asset_path):
      bucket = app.config["AWS_ASSET_BUCKET"]
      access_key = app.config["AWS_ASSET_ACCESS_KEY"]
      secret_key = app.config["AWS_ASSET_SECRET_KEY"]
      return s3.sign(bucket, asset_path, access_key, secret_key, True)
      
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
        single_character_unlock_requirement=single_character_unlock_requirement,
        single_character_reward=single_character_reward)
    


@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login.login"))

    visible_puzzle_ids = set(cube.get_visible_puzzle_ids(app))
    team_properties = cube.get_team_properties(app)
    return render_template("index.html", visible_puzzle_ids=visible_puzzle_ids, team_properties=team_properties)

@app.route("/round/<round_id>")
def round(round_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

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
def puzzle(puzzle_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    return render_template(
        "puzzles/%s.html" % puzzle_id,
        puzzle_id=puzzle_id)
        
@app.route("/puzzledraft/<puzzle_draft_id>")
def puzzle_draft(puzzle_draft_id):
    return render_template(
        "puzzle-drafts/%s.html" % puzzle_draft_id,
        puzzle_id=puzzle_draft_id)

@app.route("/assets/<puzzle_id>/<path:filename>")
def asset(puzzle_id, filename):
    if cube.is_puzzle_unlocked(app, puzzle_id):
        return send_from_directory("assets/%s" % puzzle_id, filename, as_attachment=True)
    else:
        abort(403)