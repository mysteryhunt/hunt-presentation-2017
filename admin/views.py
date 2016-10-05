from admin import app

from common import cube
from flask import abort, redirect, render_template, request, session, url_for

@app.route("/callqueue")
def callqueue():
    if "username" not in session:
        return redirect(url_for("login.login"))

    pending_submissions = cube.get_all_pending_submissions(app)

    return render_template(
        "callqueue.html",
        pending_submissions=pending_submissions)
