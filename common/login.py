from flask import Blueprint, redirect, render_template, request, session, url_for
from urllib2 import HTTPError

import cube

blueprint = Blueprint("login", __name__, template_folder="templates")

@blueprint.record
def record(setup_state):
    blueprint.config = setup_state.app.config

def clear_session():
    session.pop("username", None)
    session.pop("password", None)
    session.pop("usertype", None)
    session.pop("after_login_url", None)

@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["password"] = request.form["password"]
        try:
            all_teams_permission = cube.authorized(blueprint, "teams:read:*")
            if all_teams_permission:
                session["usertype"] = "writingteam"
            else:
                session["usertype"] = "solvingteam"
        except HTTPError, e:
            clear_session()
            if e.code == 401 or e.code == 403:
                return render_template(
                    "login.html",
                    error="Invalid login for user '%s'." % request.form["username"])
            raise e
        if "after_login_url" in session:
            after_login_url = session["after_login_url"]
            session.pop("after_login_url", None)
            return redirect(after_login_url)
        return redirect(url_for("index"))
    return render_template("login.html")

@blueprint.route("/logout")
def logout():
    clear_session()
    return redirect(url_for("index"))

@blueprint.route("/wrongusertype")
def wrongusertype():
    return render_template("wrongusertype.html")
