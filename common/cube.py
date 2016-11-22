import base64
import json
import urllib2

from flask import session

class CubeError(Exception):
    def __init__(self, request, http_error):
        self.request = request
        self.code = http_error.code
        self.error_message = http_error.read()

    def __str__(self):
        return "HTTP Error %d\nRequest: %s\nResponse:\n%s\n" % (
            self.code,
            self.request,
            self.error_message)

def add_auth_header(request):
    auth_token = base64.b64encode("%s:%s" % (session["username"], session["password"]))
    request.add_header("Authorization", "Basic %s" % auth_token)

def get(app, path):
    url = app.config["CUBE_API_SERVICE"] + path
    request = urllib2.Request(url)
    add_auth_header(request)
    try:
        response = urllib2.urlopen(request).read()
    except urllib2.HTTPError, e:
        raise CubeError(path, e)
    return json.loads(response)

def post(app, path, data):
    url = app.config["CUBE_API_SERVICE"] + path
    request = urllib2.Request(url)
    add_auth_header(request)
    request.add_header("Content-Type", "application/json")
    json_post_data = json.dumps(data)
    try:
        response = urllib2.urlopen(request, json_post_data).read()
    except urllib2.HTTPError, e:
        raise CubeError(path + "\n" + json_post_data, e)
    return json.loads(response)

def authorized(app, permission):
    response = get(app, "/authorized?permission=%s" % permission)
    return response["authorized"]

def get_visible_puzzle_ids(app):
    response = get(app, "/visibilities?teamId=%s" % session["username"])
    return [v["puzzleId"] for v in response["visibilities"]]

def get_puzzle_visibilities(app):
    response = get(app, "/visibilities?teamId=%s" % session["username"])
    return sorted(response["visibilities"], key=lambda v: v["puzzleId"])

def get_puzzle_visibility(app, puzzle_id):
    return get(app, "/visibilities/%s/%s" % (session["username"], puzzle_id))

def update_puzzle_visibility(app, team_id, puzzle_id, status):
    post(app, "/visibilities/%s/%s" % (team_id, puzzle_id), {
        "teamId": team_id,
        "puzzleId": puzzle_id,
        "status": status,
    })

def is_puzzle_unlocked(app, puzzle_id):
    return get_puzzle_visibility(app, puzzle_id)["status"] in ["UNLOCKED", "SOLVED"]

def get_all_puzzle_properties(app):
    response = get(app, "/puzzles?teamId=%s" % session["username"])
    return response

def get_puzzles(app):
    response = get(app, "/puzzles")
    return response["puzzles"]

def get_puzzle(app, puzzle_id):
    response = get(app, "/puzzles/%s" % puzzle_id)
    return response

def get_team_properties(app, team_id=None):
    if not team_id:
        team_id = session["username"]
    response = get(app, "/teams/%s" % team_id)
    return response

def get_submissions(app, puzzle_id):
    response = get(app, "/submissions?teamId=%s&puzzleId=%s" % (session["username"], puzzle_id))
    return response["submissions"]

def get_all_pending_submissions(app):
    response = get(app, "/submissions?status=SUBMITTED,ASSIGNED")
    return response["submissions"]

def get_submission(app, submission_id):
    return get(app, "/submissions/%d" % submission_id)

def create_submission(app, puzzle_id, submission):
    post(app, "/submissions", {
        "teamId": session["username"],
        "puzzleId": puzzle_id,
        "submission": submission,
    })

def update_submission_status(app, submission_id, status):
    post(app, "/submissions/%d" % submission_id, {
        "status": status,
    })

def get_hints(app, puzzle_id):
    response = get(app, "/hintrequests?teamId=%s&puzzleId=%s" % (session["username"], puzzle_id))
    return response["hintRequests"]

def get_all_pending_hint_requests(app):
    response = get(app, "/hintrequests")
    return response["hintRequests"]

def get_hint_request(app, hint_request_id):
    return get(app, "/hintrequests/%d" % hint_request_id)

def create_hint_request(app, puzzle_id, request):
    post(app, "/hintrequests", {
        "teamId": session["username"],
        "puzzleId": puzzle_id,
        "request": request,
    })

def update_hint_request(app, hint_request_id, status, response):
    post(app, "/hintrequests/%d" % hint_request_id, {
        "status": status,
        "response": response,
    })

def get_interactions(app, puzzle_id):
    response = get(app, "/interactionrequests?teamId=%s&puzzleId=%s" % (session["username"], puzzle_id))
    return response["interactionRequests"]

def get_all_pending_interaction_requests(app):
    response = get(app, "/interactionrequests")
    return response["interactionRequests"]

def get_interaction_request(app, interaction_request_id):
    return get(app, "/interactionrequests/%d" % interaction_request_id)

def create_interaction_request(app, puzzle_id, request):
    post(app, "/interactionrequests", {
        "teamId": session["username"],
        "puzzleId": puzzle_id,
        "request": request,
    })

def update_interaction_request(app, interaction_request_id, status, response):
    post(app, "/interactionrequests/%d" % interaction_request_id, {
        "status": status,
        "response": response,
    })

def get_teams(app):
    response = get(app, "/teams")
    return response["teams"]

def get_team(app, team_id):
    return get(app, "/teams/%s" % team_id)

def update_team(app, team_id, team):
    post(app, "/teams/%s" % team_id, team)

def create_team(app, team):
    post(app, "/teams", team)

def get_users(app):
    response = get(app, "/users")
    return response["users"]

def get_user(app, username):
    return get(app, "/users/%s" % username)

def update_user(app, username, user):
    post(app, "/users/%s" % username, user)

def create_user(app, user):
    post(app, "/users", user)

def create_event(app, event):
    post(app, "/events", event)
