from submit import app

from common import cube
from flask import abort, redirect, render_template, request, session, url_for

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login.login"))

    puzzle_visibilities = cube.get_puzzle_visibilities(app)
    puzzle_visibilities = [v for v in puzzle_visibilities if v.get('status','') in ['UNLOCKED','SOLVED']]
    puzzle_properties = cube.get_all_puzzle_properties(app)
    puzzle_properties = { puzzle.get('puzzleId'): puzzle for puzzle in puzzle_properties.get('puzzles',[]) }
    print(puzzle_properties)
    return render_template("index.html",
        puzzle_visibilities=puzzle_visibilities,
        puzzle_properties=puzzle_properties)

@app.route("/puzzle/<puzzle_id>", methods=["GET", "POST"])
def puzzle(puzzle_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    if request.method == "POST":
        if "submission" in request.form:
            cube.create_submission(app, puzzle_id, request.form["submission"])
        elif "hintrequest" in request.form:
            cube.create_hint_request(app, puzzle_id, request.form["hintrequest"])
        else:
            abort(400)

    submissions = cube.get_submissions(app, puzzle_id)
    visibility = cube.get_puzzle_visibility(app, puzzle_id)
    hints = cube.get_hints(app, puzzle_id)

    return render_template(
        "puzzle.html",
        puzzle_id=puzzle_id,
        submissions=submissions,
        visibility=visibility,
        hints=hints)
