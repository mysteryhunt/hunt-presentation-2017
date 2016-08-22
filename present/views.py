from present import app

from common import cube
from flask import redirect, render_template, request, send_from_directory, session, url_for

@app.context_processor
def utility_processor():
    def submit_url_for(puzzle_id):
        return app.config["SUBMIT_URL"] % puzzle_id
    return dict(submit_url_for=submit_url_for)

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login.login"))

    visible_puzzle_ids = set(cube.get_visible_puzzle_ids(app))
    return render_template("rounds/round_1.html", visible_puzzle_ids=visible_puzzle_ids)

@app.route("/puzzle/<puzzle_id>")
def puzzle(puzzle_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if not cube.is_puzzle_unlocked(app, puzzle_id):
        abort(403)

    return render_template(
        "puzzles/%s.html" % puzzle_id,
        puzzle_id=puzzle_id)

@app.route("/assets/<puzzle_id>/<path:filename>")
def asset(puzzle_id, filename):
    if cube.is_puzzle_unlocked(app, puzzle_id):
        return send_from_directory("assets/%s" % puzzle_id, filename, as_attachment=True)
    else:
        abort(403)
