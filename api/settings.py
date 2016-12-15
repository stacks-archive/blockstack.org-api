import os
import re
import subprocess


def get_settings_from_heroku(app_name):
    proc = subprocess.Popen(
        ["heroku config --app " + app_name],
        stdout=subprocess.PIPE, shell=True)

    (out, err) = proc.communicate()
    lines = out.split('\n')

    settings = {}

    for line in lines:
        parts = line.split(': ')
        if len(parts) == 2:
            name, value = parts
            settings[name] = value.strip()

    return settings


if 'DYNO' in os.environ:
    APP_URL = 'https://blockstack-site-api.herokuapp.com'

    # Debugging
    DEBUG = False

    # Secret settings
    for env_variable in os.environ:
        env_value = os.environ[env_variable]
        exec(env_variable + " = '" + env_value + "'")
else:
    APP_URL = 'localhost:5000'

    # Debugging
    DEBUG = True

    # Secret settings
    settings = get_settings_from_heroku("blockstack-site-api")
    for env_variable in settings:
        env_value = settings[env_variable]
        command = env_variable + " = '" + env_value + "'"
        exec(command)
