from app import db, login
from datetime import datetime
from sqlalchemy import or_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    matches = db.relationship('Match', 
        secondary='user_match', 
        primaryjoin="user_match.c.user_id == user.c.id",
        lazy='subquery', 
        backref=db.backref('players', lazy=True)
    )

    won_matches = db.relationship('Match',
        secondary='user_match',
        primaryjoin="and_(user_match.c.user_id == user.c.id, user_match.c.win == True)",
        backref=db.backref('winning_players')
    )
    lost_matches = db.relationship('Match',
        secondary='user_match',
        primaryjoin="and_(user_match.c.user_id == user.c.id, user_match.c.win == False)",
        backref=db.backref('losing_players')
    )

    def __repr__(self):
        return f'<User - username:{self.username}; id:{self.id}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class UserMatch(db.Model):
    __tablename__ = 'user_match'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), primary_key=True)
    win = db.Column(db.Boolean)

    user = db.relationship('User', foreign_keys=user_id)
    match = db.relationship('Match', foreign_keys=match_id)


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner_score = db.Column(db.Integer)
    loser_score = db.Column(db.Integer)
    importance = db.Column(db.Integer, default=16)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'))

    def __repr__(self):
        return f'<Match - match_id:{self.id}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    elo = db.Column(db.Integer)
    trueskill = db.Column(db.Integer)

    def __repr__(self):
        return f'<Rating for user{self.user_id}>'


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    k = db.Column(db.Integer)

    def __repr__(self):
        return f"<Table - Id {self.id} ;name {self.name}"