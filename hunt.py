from flask import Flask, abort, escape, redirect, render_template, request, send_from_directory, session, url_for
import time
import pytz
from datetime import datetime
import urllib2
import base64
import json
app = Flask(__name__)

# set the secret key.  keep this really secret:
app.secret_key = '9dsj38gj3j9fcjsaojfADf8'
app.base_service_url = 'http://localhost:8182'

def service_get_call(username, password, path):
    url = app.base_service_url + path
    request = urllib2.Request(url)
    base64string = base64.b64encode('%s:%s' % (username, password))
    request.add_header("Authorization", "Basic %s" % base64string) 
    result = urllib2.urlopen(request).read()
    return json.loads(result)
    
def service_post_call(username, password, path, data):
    url = app.base_service_url + path
    request = urllib2.Request(url)
    base64string = base64.b64encode('%s:%s' % (username, password))
    request.add_header("Authorization", "Basic %s" % base64string)
    request.add_header("Content-Type", "application/json")  
    json_post_data = json.dumps(data)
    result = urllib2.urlopen(request, json_post_data).read()
    return json.loads(result)
    
@app.errorhandler(403)
def unauthorized(e):
    return 'You are not authorized'
    
@app.route('/')
def index():
    if 'username' in session:
        visibilities = get_visibilities_for_team(session['username'])
        return render_template("hunt.html", username = session['username'], visibilities_for_team = visibilities)
    return 'You are not logged in'

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        session['username'] = request.form['username']
        session['password'] = request.form['password']
        #TODO: We should check for correctness in here
        return redirect(url_for('index'))
    return render_template("login_form.html")
    
@app.route("/submissions/<solvable_id>", methods=['GET', 'POST'])
def submissions(solvable_id):
    if request.method == 'POST':
        response = service_post_call(session['username'], session['password'], '/submissions',
            { 'teamId': session['username'], 'puzzleId': solvable_id, 'submission': request.form['submission']})
        return redirect(url_for('submissions', solvable_id=solvable_id))
    if is_authorized(solvable_id):
        submissions_obj = service_get_call(session['username'], session['password'], '/submissions?teamId=%s&puzzleId=%s' % (session['username'], solvable_id))
        print submissions_obj['submissions']
        return render_template("submission_form.html", solvable_id=solvable_id, submissions = submissions_obj['submissions'])

@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    session.pop('password', None)
    return redirect(url_for('index'))

@app.route("/assets/<solvable_id>/<path:filename>")
def secure_asset(solvable_id, filename):
    if is_authorized(solvable_id):
        return send_from_directory("assets", filename, as_attachment=True)
    else:
        abort(403)

@app.route("/rounds/<solvable_id>")
@app.route("/puzzles/<solvable_id>")
def puzzle(solvable_id):
    if is_authorized(solvable_id):
        return render_template("round_1/cr_1_puzzle_a.html")
    else:
        abort(403)
   
    
def is_authorized(solvable_id):
    if 'username' not in session or 'password' not in session:
        return False
    visibilities = service_get_call(session['username'], session['password'], '/visibilities?teamId=%s&puzzleId=%s' % (session['username'], solvable_id))
    if not visibilities:
        return False
    visibilities = visibilities['visibilities']
    if not visibilities:
        return False
    visibility = visibilities[0]
    if not visibility:
        return False
    status = visibility['status']
    if status == 'UNLOCKED' or status == 'SOLVED':
        return True
    return False
    
    
def get_visibilities_for_team(team_id):
    visibilities = service_get_call(session['username'], session['password'], '/visibilities?teamId=%s' % team_id)
    visibilities = visibilities['visibilities']
    visibilities = {v['puzzleId']: v['status'] for v in visibilities}
    return visibilities
    
@app.context_processor
def utility_processor():
    def is_unlocked(puzzleId, visibilities_for_team):
        return puzzleId in visibilities_for_team and \
                (visibilities_for_team[puzzleId] == 'UNLOCKED' or visibilities_for_team[puzzleId] == 'SOLVED')
    return dict(is_unlocked=is_unlocked)
    
@app.template_filter('datetime')
def format_datetime(value):
    fmt = '%Y-%m-%d %H:%M:%S %Z%z'
    utc = pytz.utc
    eastern = pytz.timezone('US/Eastern')
    utc_dt = utc.localize(datetime.utcfromtimestamp(value / 1000))
    eastern_dt = utc_dt.astimezone(eastern)
    return eastern_dt.strftime(fmt)

if __name__ == "__main__":
    app.run(threaded=True)