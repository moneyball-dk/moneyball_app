from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, IntegerField, SelectField, DateField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField, QuerySelectField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Optional
from wtforms.ext.dateutil.fields import DateTimeField
from app.models import User, Company
from datetime import datetime
from dateutil.tz import gettz
from flask_login import current_user
tz = gettz('Europe/Copenhagen')

def get_companies():
    return Company.query.all()

def get_players_from_company():
    players = User.query.filter_by(company_id=current_user.company_id).all()
    return sorted_users(players)

def get_players():
    players = User.query.all()
    return sorted_users(players)

def sorted_users(users):
    return sorted(
        [u for u in users],
        key=lambda x: (
            x.get_recent_match_timestamp(),
            x.shortname),
        reverse=True
        ) 
class LoginForm(FlaskForm):
    shortname = StringField('Shortname', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    shortname = StringField('Shortname (eg KWIL)', validators=[DataRequired()])
    nickname = StringField('Nickname (Eg Flying Cobra)', validators=[DataRequired()])
    company = QuerySelectField (
        'Company', 
        query_factory=get_companies,
        allow_blank=True)
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
        query_factory = get_players,
        id='selectpicker_w',
          )
    losers = QuerySelectMultipleField(
        'Losers',
        validators=[DataRequired()],
        query_factory = get_players,
        id='selectpicker_l',
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
    timestamp = DateTimeField("Match played at", default=copenhagen_now,
        id='datepick')
    submit = SubmitField('Submit')


    def validate_losers(self, losers):
        for l in losers.data:
            if l in self.winners.data:
                raise ValidationError('Same user cannot be both winner and loser')

class EditUserForm(FlaskForm):
    shortname = StringField('Shortname', validators=[DataRequired()])
    nickname = StringField('Nickname', validators=[DataRequired()])
    company = QuerySelectField ('Company', 
        query_factory=get_companies, allow_blank=True)
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

class ChooseBestMatchupForm(FlaskForm):
    players = QuerySelectMultipleField(
        'Players',
        validators=[DataRequired()],
        query_factory = sort_players,
        id='selectpicker_best',
          )
    rating_type = SelectField('Rating to use',
        choices=[
            ('elo', 'Elo'),
            ('trueskill', 'Trueskill'),
            ('goal_difference', 'Goal difference'),
            ('matches_played', 'Matches Played'),
            ],
        default='elo')
    submit = SubmitField('Submit')
class SelectPlotResampleForm(FlaskForm):
    resample_interval = SelectField('Plotting Interval',
        choices=[
            ('D', 'Daily'),
            ('W', 'Weekly')
        ],
        default='D',
        id='selectpicker_resample')
    submit = SubmitField('Submit')

class CreateCompanyForm(FlaskForm):
    name = StringField('Company Name', validators=[DataRequired()])
    submit = SubmitField('Submit')
