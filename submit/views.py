from submit import app

from common import cube, login_required
from flask import abort, redirect, render_template, request, session, url_for
from requests.exceptions import RequestException

@app.errorhandler(Exception)
def handle_exception(error):
    error_string = str(error)
    if isinstance(error, RequestException) and error.response is not None:
        error_string += ": " + error.response.json()
    return render_template(
        "error.html",
        error=error_string)

@app.errorhandler(403)
def handle_forbidden(error):
    return render_template(
        "error.html",
        error=error)

@app.errorhandler(404)
def handle_not_found(error):
    return render_template(
        "error.html",
        error=error)

@app.errorhandler(500)
def handle_internal_server_error(error):
    return render_template(
        "error.html",
        error=error)

@app.context_processor
def utility_processor():
    def puzzle_url_for(puzzle_id):
        if puzzle_id in ['fighter','wizard','cleric','linguist','economist','chemist','dynast','dungeon',
                'thespians','bridge','criminal','minstrels','cube','warlord']:
            return '/round/' + puzzle_id
        return '/puzzle/' + puzzle_id

    return dict(puzzle_url_for=puzzle_url_for)


@app.route("/")
def index():
    # Disable this route, it's not styled.
    abort(404)
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
    puzzle = cube.get_puzzle(app, puzzle_id)
    visibility = cube.get_puzzle_visibility(app, puzzle_id)
    hints = cube.get_hints(app, puzzle_id)
    interactions = cube.get_interactions(app, puzzle_id)

    return render_template(
        "puzzle.html",
        puzzle_id=puzzle_id,
        puzzle=puzzle,
        submissions=submissions,
        visibility=visibility,
        hints=hints,
        interactions=interactions)
