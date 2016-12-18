import base64
import json
import urllib2

from flask import session
import requests

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

def create_requests_session(username, password):
    s = requests.Session()
    s.auth = (username, password)
    return s

def get(app, path, username=None, password=None, requests_session=None):
    if not requests_session:
        if not username:
            username = session["username"]
        if not password:
            password = session["password"]
        requests_session = create_requests_session(username, password)
    url = app.config["CUBE_API_SERVICE"] + path
    try:
        r = requests_session.get(url)
        return r.json()
    except requests.exceptions.RequestException, e:
        raise CubeError(path, e)

def post(app, path, data, username=None, password=None, requests_session=None):
    if not requests_session:
        if not username:
            username = session["username"]
        if not password:
            password = session["password"]
        requests_session = create_requests_session(username, password)
    url = app.config["CUBE_API_SERVICE"] + path
    headers = { "Content-Type": "application/json" }
    json_post_data = json.dumps(data)
    try:
        r = requests_session.post(url, data=json_post_data, headers=headers)
        return r.json()
    except requests.exceptions.RequestException, e:
        raise CubeError(path + "\n" + json_post_data, e)
    

def authorized(app, permission):
    response = get(app, "/authorized?permission=%s" % permission)
    return response["authorized"]

def get_visible_puzzle_ids(app):
    response = get(app, "/visibilities?teamId=%s" % session["username"])
    return [v["puzzleId"] for v in response["visibilities"]]

def get_puzzle_visibilities(app):
    response = get(app, "/visibilities?teamId=%s" % session["username"])
    return sorted(response["visibilities"], key=lambda v: v["puzzleId"])

def get_puzzle_visibilities_for_list(app, puzzle_ids, team_id=None, password=None):
    if not team_id:
        team_id = session["username"]
    response = get(app, "/visibilities?teamId=%s&puzzleId=%s" % (team_id, ','.join(puzzle_ids)), \
        username = team_id, password = password)
    return { v["puzzleId"]: v for v in response["visibilities"] }

def get_puzzle_visibility(app, puzzle_id, team_id=None, password=None):
    if not team_id:
        team_id = session["username"]
    return get(app, "/visibilities/%s/%s" % (team_id, puzzle_id), username=team_id, password=password)

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

def get_all_puzzle_properties_for_list(app, puzzle_ids, team_id=None, password=None):
    if not team_id:
        team_id = session["username"]
    response = get(app, "/puzzles?teamId=%s&puzzleId=%s" % (team_id, ','.join(puzzle_ids)),
        username=team_id, password=password)
    return {puzzle.get('puzzleId'): puzzle for puzzle in response.get('puzzles',[])}

def get_puzzles(app):
    response = get(app, "/puzzles")
    return response["puzzles"]

def get_puzzle(app, puzzle_id, team_id=None, password=None):
    response = get(app, "/puzzles/%s" % puzzle_id, username=team_id, password=password)
    return response

def get_team_properties(app, team_id=None, password=None):
    if not team_id:
        team_id = session["username"]
    response = get(app, "/teams/%s" % team_id, username=team_id, password=password)
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
