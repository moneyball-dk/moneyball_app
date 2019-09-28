"""
Flask application instance
"""
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)
login = LoginManager(app=app)
login.login_view = 'login'
boostrap = Bootstrap(app=app)
moment = Moment(app)

# admin panels
from app.models import User, Company, Match, Rating
admin = Admin(app)
admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Company, db.session))
admin.add_view(ModelView(Match, db.session))
admin.add_view(ModelView(Rating, db.session))

if app.config['LOG_TO_STDOUT']:
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    app.logger.addHandler(stream_handler)
else:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/moneyball.log',
        maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s '
        '[in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)


from app import routes, models