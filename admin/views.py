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

@app.route("/teams", methods=["GET", "POST"])
def teams():
    if "username" not in session:
        return redirect(url_for("login.login"))

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
def team(team_id):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
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
        return redirect(url_for("teams"))

    team = cube.get_team(app, team_id)

    return render_template(
        "team.html",
        team=team)

def build_roles_list(form):
    roles = []
    for key, value in form.iteritems():
        if key.startswith("role_") and value:
            roles.append(key[5:])
    return roles

@app.route("/users", methods=["GET", "POST"])
def users():
    if "username" not in session:
        return redirect(url_for("login.login"))

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
def user(username):
    if "username" not in session:
        return redirect(url_for("login.login"))

    if request.method == "POST":
        update = {
            "username": username,
        }

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
