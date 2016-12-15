import json

from flask import request, Response, jsonify
from flask_crossdomain import crossdomain

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

from . import app


class APIError(Exception):
    status_code = 500
    message = "Internal server error"

    def __init__(self, message=None, status_code=None, payload=None):
        Exception.__init__(self)
        if message:
            self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        d = dict(self.payload or ())
        d['message'] = self.message
        d['type'] = camelcase_to_snakecase(
            self.__class__.__name__.replace('Error', ''))
        return d

    def __str__(self):
        return self.message


@app.route('/', methods=['GET'])
@crossdomain(origin='*')
def index():
    resp = {
        "routes": [
            '/v1/blog-rss',
            '/v1/slack-users'
        ]
    }
    return jsonify(resp), 200


@app.route('/v1/blog-rss', methods=['GET'])
@crossdomain(origin='*')
def get_blog_rss():
    try:
        resp = requests.get("http://the-blockstack-blog.ghost.io/rss/")
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()
    return Response(resp.text, mimetype='text/xml')


@app.route('/v1/slack-users', methods=['GET'])
@crossdomain(origin='*')
def get_slack_users():
    try:
        resp = requests.get('https://slack.com/api/users.list?token=' + SLACK_API_TOKEN)
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()
    resp_data = json.loads(resp.text)
    user_count = len(resp_data.get("members", 0))
    resp = {
        "user_count": user_count
    }
    return jsonify(resp), 200