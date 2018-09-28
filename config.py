import os
basedir = os.path.abspath(os.path.dirname(__file__)) # Get cwd

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'lol-this-is-so-unsafe'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False