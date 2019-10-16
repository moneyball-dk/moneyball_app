"""
Flask application instance
"""
import logging
from logging.handlers import SMTPHandler, RotatingFileHandler
import os

from flask import Flask, redirect, url_for
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import flask_login
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment
import flask_admin
from flask_admin import Admin
from flask_admin import helpers, expose
from flask_admin.contrib.sqla import ModelView

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)
login = LoginManager(app=app)
login.login_view = 'login'
boostrap = Bootstrap(app=app)
moment = Moment(app)

class MoneyballModelView(ModelView):
    def is_accessible(self):
        return flask_login.current_user.is_authenticated

    def inaccessible_callback(self, name, **kwargs):
        # redirect to login page if user doesn't have access
        return redirect(url_for('login', next=request.url))

class MyAdminIndexView(flask_admin.AdminIndexView):
    @expose('/')
    def index(self):
        from app.tasks import create_user
        admins = User.query.filter(User.is_admin).all()
        if len(admins) == 0:
            create_user(shortname = "ADMIN", nickname = "admin", password = "admin", company = None, is_admin = 1)
        if (not flask_login.current_user.is_authenticated) or (not flask_login.current_user.is_admin):
            return redirect(url_for('index'))
        return super(MyAdminIndexView, self).index()
# admin panels

from app.models import User, Company, Match, Rating
admin = Admin(app, index_view=MyAdminIndexView())
admin.add_view(MoneyballModelView(User, db.session))
admin.add_view(MoneyballModelView(Company, db.session))
admin.add_view(MoneyballModelView(Match, db.session))
admin.add_view(MoneyballModelView(Rating, db.session))

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