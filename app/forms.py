from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, IntegerField, SelectField, DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Optional
from wtforms.ext.dateutil.fields import DateTimeField
from app.models import User
from datetime import datetime
from dateutil.tz import gettz

tz = gettz('Europe/Copenhagen')


class LoginForm(FlaskForm):
    shortname = StringField('Shortname', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    shortname = StringField('Shortname (eg KWIL)', validators=[DataRequired()])
    nickname = StringField('Nickname (Eg Flying Cobra)', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat password', validators=[DataRequired(), EqualTo('password')]
        )
    submit = SubmitField('Register')

    def validate_shortname(self, shortname):
        user = User.query.filter_by(shortname=shortname.data.upper()).first()
        if user is not None:
            raise ValidationError('Please use a different shortname')

    def validate_nickname(self, nickname):
        user = User.query.filter_by(nickname=nickname.data).first()
        if user is not None:
            raise ValidationError('Please use a different nickname')

def my_check_scores(form, field):
    if form.winner_score.data <= form.loser_score.data:
        raise ValidationError('Winning score must be greater than losing score')

def sort_players():
    return sorted(
        [u for u in User.query.all()],
        key=lambda x: (
            x.get_recent_match_timestamp(),
            x.shortname),
        reverse=True
        )

def copenhagen_now():
    return datetime.now(tz=tz)

class CreateMatchForm(FlaskForm):
    winners = QuerySelectMultipleField(
        'Winners',
        validators=[DataRequired()],
        query_factory = sort_players,
          )
    losers = QuerySelectMultipleField(
        'Losers',
        validators=[DataRequired()],
        query_factory = sort_players,
          )
    winner_score = SelectField('Winning Score',
        choices=[(k, k) for k in range(11)],
        coerce=int,
        default=10,
        validators=[my_check_scores]) 
    loser_score= SelectField('Losing Score',
        choices=[(k, k) for k in range(11)],
        coerce=int,
        default=0,
        validators=[my_check_scores]) 

    importance = SelectField('Match Importance',
        choices=[(k, k) for k in [8, 16, 32]],
        coerce=int,
        default=16)
    timestamp = DateTimeField("Match played at", default=copenhagen_now, id='datepick')
    submit = SubmitField('Submit')


    def validate_losers(self, losers):
        for l in losers.data:
            if l in self.winners.data:
                raise ValidationError('Same user cannot be both winner and loser')


class EditUserForm(FlaskForm):
    shortname = StringField('Shortname', validators=[DataRequired()])
    nickname = StringField('Nickname', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditPasswordForm(FlaskForm):
    password = PasswordField('New password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat new password', validators=[DataRequired(), EqualTo('password')]
        )
    submit = SubmitField('Submit')

class ChooseLeaderboardSorting(FlaskForm):
    sorting = SelectField('Sorting',
        choices=[
            ('elo', 'Elo'),
            ('trueskill', 'Trueskill'),
            ('goal_difference', 'Goal difference'),
            ('matches_played', 'Matches Played'),
            ],
        default='elo')
    submit = SubmitField('Submit')
