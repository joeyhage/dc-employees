from os import environ

from flask import current_app, Flask, jsonify, request
from flask_cors import cross_origin
from flask_session import Session
from werkzeug.exceptions import HTTPException

from util import app_logger, auth_util, sql_util
from util.app_util import CROSS_ORIGIN_HEADERS
from util.sql_util import SQLUtil

app = Flask(__name__, static_folder=None)
app.config['IS_DEV'] = 'DEV' in environ
logger = app_logger.create_logger('app', app.config['IS_DEV'])
logger.info('Starting up...')


def app_db() -> SQLUtil:
    return current_app.config['DC_DB']


app.config['DC_DB'] = sql_util.init_db(app)
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config['SESSION_SQLALCHEMY'] = app.config['DC_DB'].get_db()
app.config['SESSION_SQLALCHEMY_TABLE'] = 'session'
app.config['SESSION_COOKIE_SECURE'] = True

# noinspection SpellCheckingInspection
app.secret_key = environ['SESSION_SECRET']
Session(app)

with app.app_context():
    from blueprints import employee_blueprint

    requires_auth = auth_util.init_auth('app')
    app.register_blueprint(employee_blueprint.employee, url_prefix='/api/employee')


@app.route('/api/hello', methods=['GET'])
def hello():
    logger.info('GET /api/hello')
    return 'Hello!'


@app.route('/api/init-session', methods=['GET'])
@cross_origin(headers=CROSS_ORIGIN_HEADERS)
@requires_auth()
def init_session():
    logger.info('GET /api/init-session')
    return jsonify({}), 200


@app.after_request
def add_headers(response):
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'deny'
    response.headers['X-Permitted-Cross-Domain-Policies'] = 'none'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    if 'DEV' in environ:
        response.headers['Access-Control-Allow-Origin'] = 'http://localhost:3000'
    else:
        response.headers['Access-Control-Allow-Origin'] = f'https://{environ["DOMAIN"]}'
    return response


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    logger.error('%d %s HTTPException', e.code, e.name, exc_info=e)
    return e.name, e.code


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    logger.error('Uncaught application exception', exc_info=e)
    return 'Server Error', 500


if __name__ == '__main__':
    app.run()
