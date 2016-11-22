from submit import app

from common import cube, login_required
from flask import abort, redirect, render_template, request, session, url_for

@app.errorhandler(cube.CubeError)
def handle_cube_error(error):
    return render_template(
        "error.html",
        error=error)

@app.route("/")
@login_required.solvingteam
def index():
    puzzle_visibilities = cube.get_puzzle_visibilities(app)
    puzzle_visibilities = [v for v in puzzle_visibilities if v.get('status','') in ['UNLOCKED','SOLVED']]
    puzzle_properties = cube.get_all_puzzle_properties(app)
    puzzle_properties = { puzzle.get('puzzleId'): puzzle for puzzle in puzzle_properties.get('puzzles',[]) }
    return render_template("index.html",
        puzzle_visibilities=puzzle_visibilities,
        puzzle_properties=puzzle_properties)

@app.route("/puzzle/<puzzle_id>", methods=["GET", "POST"])
@login_required.solvingteam
def puzzle(puzzle_id):
    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    if request.method == "POST":
        if "submission" in request.form:
            cube.create_submission(app, puzzle_id, request.form["submission"])
        elif "hintrequest" in request.form:
            cube.create_hint_request(app, puzzle_id, request.form["hintrequest"])
        elif "interactionrequest" in request.form:
            cube.create_interaction_request(app, puzzle_id, request.form["interactionrequest"])
        else:
            abort(400)

    submissions = cube.get_submissions(app, puzzle_id)
    visibility = cube.get_puzzle_visibility(app, puzzle_id)
    hints = cube.get_hints(app, puzzle_id)
    interactions = cube.get_interactions(app, puzzle_id)

    return render_template(
        "puzzle.html",
        puzzle_id=puzzle_id,
        submissions=submissions,
        visibility=visibility,
        hints=hints,
        interactions=interactions)
