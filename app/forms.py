from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectMultipleField, IntegerField, SelectField
from wtforms.ext.sqlalchemy.fields import QuerySelectMultipleField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Optional

from app.models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign in')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat password', validators=[DataRequired(), EqualTo('password')]
        )
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email')

class CreateMatchForm(FlaskForm):
    users = User.query.all()
    winner_score = IntegerField('Winning Score', validators=[Optional()])
    loser_score = IntegerField('Losing Score', validators=[Optional()])
    winners = QuerySelectMultipleField(
        'Winners', 
        validators=[DataRequired()],
        query_factory = lambda: User.query,
        get_label='username'
          )
    losers = QuerySelectMultipleField(
        'Losers', 
        validators=[DataRequired()],
        query_factory = lambda: User.query,
        get_label='username'
          )

    importance = SelectField('Match Importance',
        choices=[(k, k) for k in [16, 32]], 
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