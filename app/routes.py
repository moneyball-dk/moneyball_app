from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

from app import app, db
from app.models import User, Match, UserMatch, Rating
from app.forms import LoginForm, RegistrationForm, CreateMatchForm
from app.plots import plot_ratings, components
import time

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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        init_ratings(user)
        flash('Congratulations! You are registered.')
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
        match = make_new_match(
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


def get_match_elo_change(match):
    Qs = []
    for players in [match.winning_players, match.losing_players]:
        elos = [p.get_current_elo() for p in players]
        avg_elo = sum(elos) / len(elos)
        Q = 10 ** (avg_elo / 400)
        Qs.append(Q)
    Q_w, Q_l = Qs
    exp_win = Q_w / (Q_w + Q_l)
    change_w = match.importance * (1 - exp_win)
    return change_w

@app.route('/recalculate_ratings')
@login_required
def route_recalculate_ratings():
    recalculate_ratings()
    flash('Recalculated ratings!')
    return redirect(url_for('index'))


def recalculate_ratings():
    users = User.query.all()
    timestamps = []
    for u in users:
        timestamps.append(Rating.query \
            .filter(Rating.user_id == u.id) \
            .filter(Rating.rating_type == 'elo') \
            .order_by(Rating.timestamp) \
            .first().timestamp )
    db.session.query(Rating).delete()
    db.session.commit()
    for u, t in zip(users, timestamps):
        init_ratings(u, t)

    matches = Match.query.order_by(Match.timestamp).all()
    for match in matches:
        update_match_ratings(match)

def init_ratings(user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now()
    r_elo = Rating(user=user, rating_type='elo', rating_value=1500, 
        timestamp=timestamp)
    r_ts_m = Rating(user=user, rating_type='trueskill_mu', 
        rating_value=25, timestamp=timestamp)
    r_ts_s = Rating(user=user, rating_type='trueskill_sigma', 
        rating_value=8.333, timestamp=timestamp)
    db.session.add_all([r_elo, r_ts_m, r_ts_s])
    db.session.commit()

def update_match_ratings(match):
    elo_change = get_match_elo_change(match)
    for p in match.winning_players:
        r = Rating(user=p, match=match, rating_type='elo', 
        rating_value=p.get_current_elo() + elo_change,
        timestamp=match.timestamp)
        db.session.add(r)
    for p in match.losing_players:
        r = Rating(user=p, match=match, rating_type='elo',
        rating_value=p.get_current_elo() - elo_change,
        timestamp=match.timestamp)
        db.session.add(r)
    db.session.commit()


@login_required
@app.route('/delete_match/<match_id>', methods=['POST'])
def route_delete_match(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    delete_match(match)
    time.sleep(2)
    flash('Match deleted')
    return redirect(url_for('index'))

def delete_match(match):
    db.session.delete(match)
    db.session.commit()
    recalculate_ratings()


def make_new_match(winners, losers, w_score, l_score, importance):
    match = Match(
        winner_score=w_score, 
        loser_score=l_score,
        importance=importance)
    db.session.add(match)
    db.session.flush()

    for w in winners:
        user_match = UserMatch(
            user=w,
            match=match, 
            win=True)
        db.session.add(user_match)
    for l in losers:
        user_match = UserMatch(
            user=l,
            match=match, 
            win=False)
        db.session.add(user_match)
    db.session.flush()
    
    update_match_ratings(match)
    db.session.commit()
    return match