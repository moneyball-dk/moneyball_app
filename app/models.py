from app import db, login
from sqlalchemy import or_, and_
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from dateutil.tz import gettz
from functools import partial

tz = gettz('Europe/Copenhagen')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    shortname = db.Column(db.String(64), index=True, unique=True)
    nickname = db.Column(db.String(128), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    matches = db.relationship('Match',
        order_by="Match.timestamp",
        secondary='user_match',
        primaryjoin="user_match.c.user_id == user.c.id",
        backref=db.backref('players', lazy=True)
    )

    won_matches = db.relationship('Match',
        order_by="Match.timestamp",
        secondary='user_match',
        primaryjoin="and_(user_match.c.user_id == user.c.id, user_match.c.win == True)",
        backref=db.backref('winning_players'),
        viewonly=True,
    )
    lost_matches = db.relationship('Match',
        order_by="Match.timestamp",
        secondary='user_match',
        primaryjoin="and_(user_match.c.user_id == user.c.id, user_match.c.win == False)",
        backref=db.backref('losing_players'),
        viewonly=True,
    )

    def __repr__(self):
        return f'<User - shortname:{self.shortname}; id:{self.id}>'

    def __str__(self):
        return f'({self.shortname}) {self.nickname}'

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

    def get_current_trueskill(self):
        mu = Rating.query \
            .filter(and_(
                Rating.user_id == self.id),
                Rating.rating_type == 'trueskill_mu') \
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

    def get_current_goal_difference(self):
        rating = Rating.query \
            .filter(and_(Rating.user_id == self.id), Rating.rating_type == 'goal_difference') \
            .order_by(Rating.timestamp.desc()) \
            .first()
        try:
            return rating.rating_value
        except AttributeError:
            return 0


    def get_match_rating_value(self, match, rating_type='elo'):
        rating = Rating.query \
            .filter(Rating.user_id == self.id) \
            .filter(Rating.match_id == match.id) \
            .filter(Rating.rating_type == rating_type) \
            .first()
        try:
            return rating.rating_value
        except AttributeError:
            return 0

    def get_current_rating(self, rating_type='elo'):
        if rating_type == 'trueskill':
            (mu, sigma) = self.get_current_trueskill()
            rating = mu - (3*sigma)
        elif rating_type == 'elo':
            rating = self.get_current_elo()
        elif rating_type == 'goal_difference':
            rating = self.get_current_goal_difference()
        else:
            raise AssertionError(f'wrong rating_type: {rating_type}')
        return rating

    def can_approve_match(self, match):
        if self in match.winning_players and not match.approved_winner:
            return True
        if self in match.losing_players and not match.approved_loser:
            return True
        else:
            return False

    def can_delete_match(self, match):
        if self in match.players: return True
        else: return False

    def get_recent_match_timestamp(self):
        sorted_matches = sorted(self.matches, key=lambda x: x.timestamp, reverse=True)
        try:
            most_recent_match = sorted_matches[0]
            return most_recent_match.timestamp
        except IndexError:
            # If no matches played, return current time
            return datetime.min

    def get_winstreak(self):
        winstreak = 0
        for m in self.matches[::-1]:
            if self in m.winning_players:
                winstreak += 1
            else:
                break
        return winstreak

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

def copenhagen_now():
    return partial(datetime.now, tz=tz)

class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    winner_score = db.Column(db.Integer)
    loser_score = db.Column(db.Integer)
    importance = db.Column(db.Integer, default=16)
    timestamp = db.Column(db.DateTime, index=True, default=copenhagen_now)
    table_id = db.Column(db.Integer, db.ForeignKey('table.id'))
    ratings = db.relationship('Rating')
    approved_winner = db.Column(db.Boolean, default=False)
    approved_loser = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Match - match_id:{self.id}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    match_id = db.Column(db.Integer, db.ForeignKey('match.id'))
    timestamp = db.Column(db.DateTime, index=True, default=copenhagen_now)
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
