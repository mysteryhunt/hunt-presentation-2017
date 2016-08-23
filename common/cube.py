import base64
import json
import urllib2

from flask import session

def add_auth_header(request):
    auth_token = base64.b64encode("%s:%s" % (session["username"], session["password"]))
    request.add_header("Authorization", "Basic %s" % auth_token)

def get(app, path):
    url = app.config["CUBE_API_SERVICE"] + path
    request = urllib2.Request(url)
    add_auth_header(request)
    response = urllib2.urlopen(request).read()
    return json.loads(response)

def post(app, path, data):
    url = app.config["CUBE_API_SERVICE"] + path
    request = urllib2.Request(url)
    add_auth_header(request)
    request.add_header("Content-Type", "application/json")
    json_post_data = json.dumps(data)
    response = urllib2.urlopen(request, json_post_data).read()
    return json.loads(response)

def authorized(app, permission):
    response = get(app, "/authorized?permission=%s" % permission)
    return response["authorized"]

def get_visible_puzzle_ids(app):
    response = get(app, "/visibilities?teamId=%s" % session["username"])
    return sorted([v["puzzleId"] for v in response["visibilities"]])

def get_puzzle_visibility(app, puzzle_id):
    return get(app, "/visibilities/%s/%s" % (session["username"], puzzle_id))

def is_puzzle_unlocked(app, puzzle_id):
    return get_puzzle_visibility(app, puzzle_id)["status"] in ["UNLOCKED", "SOLVED"]

def get_submissions(app, puzzle_id):
    response = get(app, "/submissions?teamId=%s&puzzleId=%s" % (session["username"], puzzle_id))
    return response["submissions"]

def create_submission(app, puzzle_id, submission):
    post(app, "/submissions", {
        "teamId": session["username"],
        "puzzleId": puzzle_id,
        "submission": submission,
    })
