from flask import Flask


app = Flask(__name__)
app.config.from_object('api.settings')

import api_v1