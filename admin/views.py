from admin import app

from common import cube, login_required
from flask import abort, redirect, render_template, request, session, url_for
from requests.exceptions import RequestException

import time

@app.context_processor
def utility_processor():
    def is_authorized(permission):
        return cube.authorized(app, permission)

    def current_timestamp():
        return int(time.time() * 1000)

    return {
        "is_authorized": is_authorized,
        "current_timestamp": current_timestamp,
    }

def get_puzzles():
    puzzles = cube.get_puzzles(app)
    def sortkey(puzzle):
        if "DisplayNameProperty" in puzzle["puzzleProperties"]:
            return puzzle["puzzleProperties"]["DisplayNameProperty"]["displayName"]
        else:
            return puzzle["puzzleId"]
    puzzles.sort(key=sortkey)
    return puzzles

def get_puzzle_id_to_puzzle():
    puzzles = cube.get_puzzles(app)
    return {puzzle['puzzleId']: puzzle for puzzle in puzzles}

@app.errorhandler(RequestException)
def handle_request_exception(error):
    return render_template(
        "error.html",
        error=error)

@app.route("/")
@login_required.writingteam
def index():
    return render_template("index.html")

@app.route("/callqueue")
@login_required.writingteam
def callqueue():
    pending_submissions = cube.get_all_pending_submissions(app)
    pending_hint_requests = cube.get_all_pending_hint_requests(app)
    puzzle_id_to_puzzle = get_puzzle_id_to_puzzle()

    return render_template(
        "callqueue.html",
        pending_submissions=pending_submissions,
        pending_hint_requests=pending_hint_requests,
        puzzle_id_to_puzzle=puzzle_id_to_puzzle)

@app.route("/interactionqueue")
@login_required.writingteam
def interactionqueue():
    pending_interaction_requests = cube.get_all_pending_interaction_requests(app)
    puzzle_id_to_puzzle = get_puzzle_id_to_puzzle()

    return render_template(
        "interactionqueue.html",
        pending_interaction_requests=pending_interaction_requests,
        puzzle_id_to_puzzle=puzzle_id_to_puzzle)

@app.route("/submission/<int:submission_id>", methods=["GET", "POST"])
@login_required.writingteam
def submission(submission_id):
    if request.method == "POST":
        if "status" in request.form:
            cube.update_submission_status(app, submission_id, request.form["status"])
            if request.form["status"] == "SUBMITTED":
                return redirect(url_for("callqueue"))
        else:
            abort(400)

    submission = cube.get_submission(app, submission_id)
    past_submissions = cube.get_submissions(app, submission['puzzleId'], submission['teamId'])
    past_submissions = [s for s in past_submissions if s['submissionId'] != submission_id]
    puzzle = cube.get_puzzle(app, submission['puzzleId'])
    team = cube.get_team_properties(app, team_id=submission['teamId'])

    return render_template(
        "submission.html",
        submission=submission,
        past_submissions=past_submissions,
        puzzle=puzzle,
        team=team)

@app.route("/hintrequest/<int:hint_request_id>", methods=["GET", "POST"])
@login_required.writingteam
def hintrequest(hint_request_id):
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
    puzzle = cube.get_puzzle(app, hint_request['puzzleId'])
    team = cube.get_team_properties(app, team_id=hint_request['teamId'])

    return render_template(
        "hintrequest.html",
        hint_request=hint_request,
        puzzle=puzzle,
        team=team)

@app.route("/interactionrequest/<int:interaction_request_id>", methods=["GET", "POST"])
@login_required.writingteam
def interactionrequest(interaction_request_id):
    if request.method == "POST":
        if "status" in request.form:
            response = ""
            if "response" in request.form:
                response = request.form["response"]
            cube.update_interaction_request(app, interaction_request_id, request.form["status"], response)
            if request.form["status"] == "REQUESTED":
                return redirect(url_for("interactionqueue"))
        else:
            abort(400)

    interaction_request = cube.get_interaction_request(app, interaction_request_id)
    puzzle = cube.get_puzzle(app, interaction_request['puzzleId'])
    team = cube.get_team_properties(app, team_id=interaction_request['teamId'])

    return render_template(
        "interactionrequest.html",
        interaction_request=interaction_request,
        puzzle=puzzle,
        team=team)

@app.route("/teams", methods=["GET", "POST"])
@login_required.writingteam
def teams():
    if request.method == "POST":
        cube.create_team(app, {
            "teamId": request.form["teamId"],
            "password": request.form["password"],
            "email": request.form["email"],
            "primaryPhone": request.form["primaryPhone"],
            "secondaryPhone": request.form["secondaryPhone"],
        })

    teams = cube.get_teams(app)

    return render_template(
        "teams.html",
        teams=teams)

@app.route("/team/<team_id>", methods=["GET", "POST"])
@login_required.writingteam
def team(team_id):
    if request.method == "POST":
        if request.form["action"] == "ChangeContactInfo":
            if ("email" not in request.form or
                "primaryPhone" not in request.form or
                "secondaryPhone" not in request.form):
                abort(400)
            cube.update_team(app, team_id, {
                "teamId": team_id,
                "email": request.form["email"],
                "primaryPhone": request.form["primaryPhone"],
                "secondaryPhone": request.form["secondaryPhone"],
            })
        elif request.form["action"] == "SetPuzzleStatus":
            if request.form["actionType"] == "Unlock":
                status = "UNLOCKED"
            elif request.form["actionType"] == "Solve":
                status = "SOLVED"
            else:
                abort(400)
            cube.update_puzzle_visibility(
                app,
                team_id,
                request.form["puzzleId"],
                status)
        else:
            abort(400)
        return redirect(url_for("teams"))

    team = cube.get_team(app, team_id)

    return render_template(
        "team.html",
        team=team,
        puzzles=get_puzzles())

def build_roles_list(form):
    roles = []
    for key, value in form.iteritems():
        if key.startswith("role_") and value:
            roles.append(key[5:])
    return roles

@app.route("/users", methods=["GET", "POST"])
@login_required.writingteam
def users():
    if request.method == "POST":
        cube.create_user(app, {
            "username": request.form["username"],
            "password": request.form["password"],
            "roles": build_roles_list(request.form),
        })

    users = cube.get_users(app)

    return render_template(
        "users.html",
        users=users)

@app.route("/user/<username>", methods=["GET", "POST"])
@login_required.writingteam
def user(username):
    if request.method == "POST":
        update = {
            "username": username,
        }

        if cube.authorized(app, "userroles:update:%s" % username):
            user = cube.get_user(app, username)
            roles = build_roles_list(request.form)
            if user["roles"] != roles:
                update["roles"] = roles

        logout = False
        if request.form["password"]:
            update["password"] = request.form["password"]
            if username == session["username"]:
                logout = True

        cube.update_user(app, username, update)

        if logout:
            return redirect(url_for("login.logout"))
        return redirect(url_for("users"))

    user = cube.get_user(app, username)

    return render_template(
        "user.html",
        user=user)

@app.route("/admintools", methods=["GET", "POST"])
@login_required.writingteam
def admintools():
    if request.method == "POST":
        if request.form["action"] == "HuntStart":
            cube.create_event(app, {
                "eventType": "HuntStart",
            })
        elif request.form["action"] == "FullRelease":
            cube.create_event(app, {
                "eventType": "FullRelease",
                "puzzleId": request.form["puzzleId"],
            })
        elif request.form["action"] == "FullSolve":
            cube.create_event(app, {
                "eventType": "FullSolve",
                "puzzleId": request.form["puzzleId"],
            })
        else:
            abort(400)

    return render_template(
        "admintools.html",
        puzzles=get_puzzles())
