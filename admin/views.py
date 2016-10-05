from admin import app

from common import cube
from flask import abort, redirect, render_template, request, session, url_for

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login.login"))
    return render_template("index.html")

@app.route("/callqueue")
def callqueue():
    if "username" not in session:
        return redirect(url_for("login.login"))

    pending_submissions = cube.get_all_pending_submissions(app)

    return render_template(
        "callqueue.html",
        pending_submissions=pending_submissions)

@app.route("/submission/<int:submission_id>", methods=["GET", "POST"])
def submission(submission_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
        if "status" in request.form:
            cube.update_submission_status(app, submission_id, request.form["status"])
            if request.form["status"] == "SUBMITTED":
                return redirect(url_for("callqueue"))
        else:
            abort(400)

    submission = cube.get_submission(app, submission_id)
    puzzle = cube.get_puzzle(app, submission['puzzleId'])
    team = cube.get_team_properties(app, team_id=submission['teamId'])

    return render_template(
        "submission.html",
        submission=submission,
        puzzle=puzzle,
        team=team)
