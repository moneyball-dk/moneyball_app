from app import db, login
from datetime import datetime
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shortname = db.Column(db.String(64), index=True, unique=True)
    nickname = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    matches = db.relationship('Match', 
        secondary='user_match', 
        primaryjoin="user_match.c.user_id == user.c.id",
        backref=db.backref('players', lazy=True)
    )

    won_matches = db.relationship('Match',
        secondary='user_match',
        primaryjoin="and_(user_match.c.user_id == user.c.id, user_match.c.win == True)",
        backref=db.backref('winning_players'),
        viewonly=True,
    )
    lost_matches = db.relationship('Match',
        secondary='user_match',
        primaryjoin="and_(user_match.c.user_id == user.c.id, user_match.c.win == False)",
        backref=db.backref('losing_players'),
        viewonly=True,
    )

    def __repr__(self):
        return f'<User - shortname:{self.shortname}; id:{self.id}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_current_elo(self):
        elo_q = Rating.query \
            .filter(and_(Rating.user_id == self.id), Rating.rating_type == 'elo') \
            .order_by(Rating.timestamp.desc()) \
            .first()
        try:
            return elo_q.rating_value
        except AttributeError:
            return 1500

    def get_trueskill(self):
        mu = Rating.query \
            .filter(and_(Rating.user_id == self.id), Rating.rating_type == 'trueskill_mu') \
            .order_by(Rating.timestamp.desc()) \
            .first()
        sigma = Rating.query \
            .filter(and_(
                Rating.user_id == self.id), 
                Rating.rating_type == 'trueskill_sigma') \
            .order_by(Rating.timestamp.desc()) \
            .first()
        try:
            return (mu.rating_value, sigma.rating_value)
        except AttributeError:
            return (25, 8.33)
    
    def get_match_rating_value(self, match, rating_type='elo'):
        rating = Rating.query \
            .filter(Rating.user_id == self.id) \
            .filter(Rating.match_id == match.id) \
            .filter(Rating.rating_type == 'elo') \
            .first()
        try:
            return rating.rating_value
        except AttributeError:
            return 0

@login.user_loader
def load_user(id):
    return User.query.get(int(id))

class UserMatch(db.Model):
    __tablename__ = 'user_match'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'), primary_key=True)
    win = db.Column(db.Boolean)

    user = db.relationship('User', foreign_keys=user_id)
    match = db.relationship('Match', foreign_keys=match_id )

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner_score = db.Column(db.Integer)
    loser_score = db.Column(db.Integer)
    importance = db.Column(db.Integer, default=16)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'))
    ratings = db.relationship('Rating')

    def __repr__(self):
        return f'<Match - match_id:{self.id}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.now)
    rating_type = db.Column(db.String(64), index=True)
    rating_value = db.Column(db.Float)

    user = db.relationship('User', foreign_keys=user_id)
    match = db.relationship('Match', foreign_keys=match_id)

    def __repr__(self):
        return f'<Rating - user:{self.user_id}, {self.rating_type}:{self.rating_value} @ {self.timestamp}>'


class Table(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    k = db.Column(db.Integer)

    def __repr__(self):
        return f"<Table - Id {self.id} ;name {self.name}"