import os

from dotenv import load_dotenv
from flask import Flask

from utils.redis_client import init_redis
from routes.basic import basic_bp
from routes.course import course_bp
from routes.status import status_bp

load_dotenv()

app = Flask(__name__)

app.config['DEBUG'] = os.getenv('APP_DEBUG', 'false').lower() == 'true'

# Redis SSE — init from env vars
init_redis()

# Prometheus metrics（开发环境默认关闭，生产通过 ENABLE_METRICS=true 开启）
if os.getenv('ENABLE_METRICS', '').lower() == 'true':
    from prometheus_flask_exporter import PrometheusMetrics
    PrometheusMetrics(app)

# Register route blueprints
app.register_blueprint(basic_bp)
app.register_blueprint(course_bp)
app.register_blueprint(status_bp)
