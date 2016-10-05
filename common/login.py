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

@blueprint.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        session["username"] = request.form["username"]
        session["password"] = request.form["password"]
        try:
            if "REQUIRE_TEAM_LOGIN" in blueprint.config:
                if not cube.authorized(blueprint, "teams:read:%s" % session["username"]):
                    clear_session()
                    return render_template(
                        "login.html",
                        error="Invalid team login '%s'." % request.form["username"])
            if "REQUIRE_ADMIN_LOGIN" in blueprint.config:
                if not cube.authorized(blueprint, "teams:read:*"):
                    clear_session()
                    return render_template(
                        "login.html",
                        error="Invalid admin login '%s'." % request.form["username"])
        except HTTPError, e:
            clear_session()
            if e.code == 401 or e.code == 403:
                return render_template(
                    "login.html",
                    error="Invalid login for user '%s'." % request.form["username"])
            raise e
        return redirect(url_for("index"))
    return render_template("login.html")

@blueprint.route("/logout")
def logout():
    clear_session()
    return redirect(url_for("index"))
