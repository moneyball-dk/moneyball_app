from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

from app import app, db
from app.models import User, Match, UserMatch, Rating
from app.forms import LoginForm, RegistrationForm, CreateMatchForm
from app.plots import plot_ratings, components
import time

from app import tasks

@app.route('/')
@app.route('/index')
def index():
    try:
        users = User.query.all()
        users = sorted(users, key=lambda u: u.get_current_elo(), reverse=True)
    except:
        users = None
    return render_template('index.html', title='Home', users=users)

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
        user = tasks.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        if isinstance(user, User):
            flash('Congratulations! You are registered.')
        else:
            flash('Something went wrong')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    plot = plot_ratings(username, 'elo')
    b_script, b_div = components(plot)
    return render_template('user.html', user=user, matches=user.matches, b_script=b_script, b_div=b_div)


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
        match = tasks.make_new_match(
            winners=form.winners.data,
            losers=form.losers.data,
            w_score=form.winner_score.data,
            l_score=form.loser_score.data,
            importance=form.importance.data
            )
        if isinstance(match, Match):
            flash('Match created')
        else:
            flash('Something went wrong')
        return redirect(url_for('login'))
    return render_template('create_match.html', title='Create match', form=form)


@app.route('/recalculate_ratings')
@login_required
def route_recalculate_ratings():
    tasks.recalculate_ratings()
    flash('Recalculated ratings!')
    return redirect(url_for('index'))

@login_required
@app.route('/delete_match/<match_id>', methods=['POST'])
def route_delete_match(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    tasks.delete_match(match)
    flash('Match deleted')
    return redirect(url_for('index'))