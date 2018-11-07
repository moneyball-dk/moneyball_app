from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, IntegerField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, ValidationError, EqualTo, Optional

from app.models import User

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

class CreateMatchForm(FlaskForm):
    winner_score = IntegerField('Winning Score', validators=[Optional()])
    loser_score = IntegerField('Losing Score', validators=[Optional()])
    winners = QuerySelectMultipleField(
        'Winners', 
        validators=[DataRequired()],
        query_factory = lambda: User.query,
          )
    losers = QuerySelectMultipleField(
        'Losers', 
        validators=[DataRequired()],
        query_factory = lambda: User.query,
          )

    importance = SelectField('Match Importance',
        choices=[(k, k) for k in [8, 16, 32]], 
        coerce=int, 
        default=16)
    submit = SubmitField('Submit')


    def validate_losers(self, losers):
        for l in losers.data:
            if l in self.winners.data:
                raise ValidationError('Same user cannot be both winner and loser')

    def validate_loser_score(self, loser_score):
        if self.winner_score.data <= loser_score.data:
            raise ValidationError('Winning score must be greater than losing score')


class EditUserForm(FlaskForm):
    shortname = StringField('Shortname', validators=[DataRequired()])
    nickname = StringField('Nickname', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat password', validators=[DataRequired(), EqualTo('password')]
        )
    submit = SubmitField('Submit')

class ChooseLeaderboardSorting(FlaskForm):
    sorting =SelectField('Sorting', 
        choices=[('elo', 'Elo'), ('trueskill', 'Trueskill')],
        default='elo')
    submit = SubmitField('Submit')