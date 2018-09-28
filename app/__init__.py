"""
Flask application instance
"""
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from flask_moment import Moment

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)
migrate = Migrate(app=app, db=db)
login = LoginManager(app=app)
login.login_view = 'login'
boostrap = Bootstrap(app=app)
moment = Moment(app)


from app import routes, models