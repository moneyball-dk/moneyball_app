from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

from app import app, db
from app.models import User, Match, UserMatch
from app.forms import LoginForm, RegistrationForm, CreateMatchForm

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, sent to frontpage
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations! You are registered.')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user, matches=user.matches)

@app.route('/match/<match_id>')
def match(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    return render_template('view_match.html', title='Match details', match=match)


@app.route('/create_match', methods=['GET', 'POST'])
@login_required
def create_match():
    if not current_user.is_authenticated:
        flash('You have to login before creating a match.')
        return redirect(url_for('index'))
    form = CreateMatchForm()
    if form.validate_on_submit():
        match = Match(
            winner_score=form.winner_score.data, 
            loser_score=form.loser_score.data)
        db.session.add(match)
        db.session.flush()

        for w in form.winners.data:
            user_match = UserMatch(
                user_id=w.id,
                match_id=match.id, 
                win=True)
            db.session.add(user_match)
        for l in form.losers.data:
            user_match = UserMatch(
                user_id=l.id,
                match_id=match.id, 
                win=False)
            db.session.add(user_match)
        db.session.commit()
        flash('Match created')
        return redirect(url_for('login'))
    return render_template('create_match.html', title='Create match', form=form)