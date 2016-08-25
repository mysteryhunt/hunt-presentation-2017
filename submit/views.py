from submit import app

from common import cube
from flask import abort, redirect, render_template, request, session, url_for

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login.login"))

    puzzle_visibilities = cube.get_puzzle_visibilities(app)
    return render_template("index.html", puzzle_visibilities=puzzle_visibilities)

@app.route("/puzzle/<puzzle_id>", methods=["GET", "POST"])
def puzzle(puzzle_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    if request.method == "POST":
        cube.create_submission(app, puzzle_id, request.form["submission"])

    submissions = cube.get_submissions(app, puzzle_id)
    visibility = cube.get_puzzle_visibility(app, puzzle_id)
    return render_template(
        "puzzle.html",
        puzzle_id=puzzle_id,
        submissions=submissions,
        visibility=visibility)
