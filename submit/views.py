from submit import app

from common import cube
from flask import abort, redirect, render_template, request, session, url_for

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login.login"))

    puzzle_ids = cube.get_visible_puzzle_ids(app)
    return render_template("index.html", puzzle_ids=puzzle_ids)

@app.route("/puzzle/<puzzle_id>", methods=["GET", "POST"])
def puzzle(puzzle_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    if request.method == "POST":
        cube.create_submission(app, puzzle_id, request.form["submission"])

    submissions = cube.get_submissions(app, puzzle_id)
    return render_template(
        "puzzle.html",
        puzzle_id=puzzle_id,
        submissions=submissions)
