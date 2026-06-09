import configparser
from flask import Flask

from utils.redis_client import init_redis
from routes.basic import basic_bp
from routes.course import course_bp
from routes.status import status_bp

app = Flask(__name__)

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini', encoding='utf-8')

IS_DEBUG = CONFIG['Switch']['debug']  # 1 / 0

# Redis connection for SSE streaming — all values required in config.ini [Redis] section
init_redis(CONFIG['Redis'])

# Register route blueprints
app.register_blueprint(basic_bp)
app.register_blueprint(course_bp)
app.register_blueprint(status_bp)
