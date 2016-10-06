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
    pending_hint_requests = cube.get_all_pending_hint_requests(app)

    return render_template(
        "callqueue.html",
        pending_submissions=pending_submissions,
        pending_hint_requests=pending_hint_requests)

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

@app.route("/hintrequest/<int:hint_request_id>", methods=["GET", "POST"])
def hintrequest(hint_request_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
        if "status" in request.form:
            response = ""
            if "response" in request.form:
                response = request.form["response"]
            cube.update_hint_request(app, hint_request_id, request.form["status"], response)
            if request.form["status"] == "REQUESTED":
                return redirect(url_for("callqueue"))
        else:
            abort(400)

    hint_request = cube.get_hint_request(app, hint_request_id)
    team = cube.get_team_properties(app, team_id=hint_request['teamId'])

    return render_template(
        "hintrequest.html",
        hint_request=hint_request,
        team=team)
