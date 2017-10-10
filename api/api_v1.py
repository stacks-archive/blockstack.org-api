import re
import json
from flask import request, Response, jsonify
from flask_crossdomain import crossdomain
import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import Timeout as RequestsTimeout

from . import app
from .settings import SLACK_API_TOKEN


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
            '/v1/domain-stats',
            '/v1/slack-users',
            '/v1/forum-users',
            '/v1/meetup-users',
            '/v1/stats'
        ]
    }
    return jsonify(resp), 200


@app.route('/v1/blog-rss', methods=['GET'])
@crossdomain(origin='*')
def get_blog_rss():
    page_number = request.args.get('page') or '1'

    try:
        resp = requests.get("https://blockstack.ghost.io/rss/" + page_number)
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()

    if resp.status_code == 404:
        return Response("", mimetype='text/xml')

    rss_text = resp.text

    rss_text = rss_text.replace(
        "http://blockstack.ghost.io/content/images/",
        "https://blockstack.ghost.io/content/images/")
    rss_text = rss_text.replace(
        "<link>https://blockstack.ghost.io/",
        "<link>https://blockstack.org/blog/")
    rss_text = rss_text.replace(
        "href=\"https://blockstack.ghost.io/rss/\"",
        "href=\"https://blockstack-site-api.herokuapp.com/v1/blog-rss\"")

    return Response(rss_text, mimetype='text/xml')

@app.route('/v1/prices', methods=['GET'])
@crossdomain(origin='*')
def get_prices():
    try:
        resp = requests.get("https://api.coinmarketcap.com/v1/ticker/?limit=20")
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()

    resp_data = json.loads(resp.text)

    return jsonify(resp_data), 200


@app.route('/v1/domain-stats', methods=['GET'])
@crossdomain(origin='*')
def get_domain_stats():
    user_count = 0

    try:
        resp = requests.get("https://core.blockstack.org/v1/blockchains/bitcoin/name_count")
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()

    resp_data = json.loads(resp.text)
    if "names_count" in resp_data:
        user_count = resp_data["names_count"]

    return jsonify({
        "domain_count": user_count
    }), 200


@app.route('/v1/slack-users', methods=['GET'])
@crossdomain(origin='*')
def get_slack_users():
    try:
        resp = requests.get('https://slack.com/api/users.list?token=' + SLACK_API_TOKEN)
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()
    
    try:
        resp_data = json.loads(resp.text)
    except ValueError:
        raise APIError("Invalid response from Slack")

    user_count = len(resp_data.get("members", []))
    
    return jsonify({
        "user_count": user_count
    }), 200


@app.route('/v1/forum-users', methods=['GET'])
@crossdomain(origin='*')
def get_forum_users():
    user_count = 0

    try:
        resp = requests.get('https://forum.blockstack.org/groups/trust_level_0.json')
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()

    resp_data = json.loads(resp.text)
    if "basic_group" in resp_data:
        basic_group = resp_data["basic_group"]
        if "user_count" in basic_group:
            user_count = basic_group["user_count"]

    return jsonify({
        "user_count": user_count
    }), 200


@app.route('/v1/meetup-users', methods=['GET'])
@crossdomain(origin='*')
def get_meetup_users():
    user_count = 0

    try:
        resp = requests.get('https://www.meetup.com/topics/blockstack/')
    except (RequestsConnectionError, RequestsTimeout) as e:
        raise APIError()

    html = resp.text
    pattern = re.compile("<p class=\"text--bold\">(.*)</p>")
    matches = pattern.findall(html)

    if len(matches):
        user_count = int(matches[0].replace(',', ''))

    return jsonify({
        "user_count": user_count
    }), 200


@app.route('/v1/stats', methods=['GET'])
@crossdomain(origin='*')
def get_stats():
    slack_users = forum_users = meetup_users = domains = 0
    try:
        slack_users = json.loads(get_slack_users().response[0])['user_count']
    except:
        pass

    try:
        forum_users = json.loads(get_forum_users().response[0])['user_count']
    except:
        pass

    try:
        meetup_users = json.loads(get_meetup_users().response[0])['user_count']
    except:
        pass

    try:
        domains = json.loads(get_domain_stats().response[0])['domain_count']
    except:
        pass

    resp = {
        "slack_users": slack_users,
        "forum_users": forum_users,
        "meetup_users": meetup_users,
        "domains": domains
    }

    return jsonify(resp), 200
