from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

from app import app, db
from app.models import User, Match, UserMatch, Rating
from app.forms import LoginForm, RegistrationForm, CreateMatchForm, EditUserForm, ChooseLeaderboardSorting
from app.forms import LoginForm, RegistrationForm, CreateMatchForm, EditUserForm, EditPasswordForm, ChooseLeaderboardSorting
from app.plots import plot_ratings
import time

from app import tasks

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index(sorting='elo'):
    form = ChooseLeaderboardSorting()
    sorting = form.sorting.data
    users = User.query.all()
    users = sorted(users, key=lambda u: u.get_current_rating(rating_type=sorting), reverse=True)
    return render_template('index.html', title='Home', users=users, form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, sent to frontpage
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(shortname=form.shortname.data.upper()).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid shortname or password.')
            return redirect(url_for('login'))
        flash(f'{user.shortname} successfully logged in')
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign in', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash(f'User logged out')
    return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = tasks.create_user(
            shortname=form.shortname.data.upper(),
            nickname=form.nickname.data,
            password=form.password.data
        )
        if isinstance(user, User):
            flash('Congratulations! You are registered.')
        else:
            flash('Something went wrong')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<user_id>')
def user(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    b_div = plot_ratings(user.shortname, 'elo')
    #b_script, b_div = components(plot)

    return render_template('user.html', user=user, matches=user.matches, 
        b_div=b_div, title='User')


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
        if not current_user in form.winners.data + form.losers.data:
            flash('Logged in user should be playing in match')
            return redirect(url_for('create_match'))
        match = tasks.make_new_match(
            winners=form.winners.data,
            losers=form.losers.data,
            w_score=form.winner_score.data,
            l_score=form.loser_score.data,
            importance=form.importance.data,
            user_creating_match=current_user,
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

@app.route('/delete_match/<match_id>', methods=['POST'])
@login_required
def route_delete_match(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    tasks.delete_match(match)
    flash('Match deleted')
    return redirect(url_for('index'))

@app.route('/edit_user', methods=['GET', 'POST'])
@login_required
def route_edit_user():
    user_id = current_user.id
    return route_edit_other_user(user_id)

@app.route('/user/<user_id>/edit', methods=['GET', 'POST'])
def route_edit_other_user(user_id):
    form = EditUserForm()
    user = User.query.filter_by(id=user_id).first_or_404()
    if form.validate_on_submit():
        shortname = form.shortname.data.upper()
        sn_user = User.query.filter_by(shortname=shortname).first()
        if sn_user is not None and sn_user.id != user.id:
            flash('That shortname is already taken')
            return redirect(url_for('route_edit_user', user_id=user.id))
        nn_user = User.query.filter_by(nickname=form.nickname.data).first()
        if nn_user is not None and nn_user != user:
            flash('That nickname is already taken')
            return redirect(url_for('route_edit_user', user_id=user.id))
        tasks.update_user(
            user=user,
            shortname=shortname,
            nickname=form.nickname.data,
        )
        flash(f'User {user} updated')
        return redirect(url_for('user', user_id=user.id))
    elif request.method == 'GET':
        form.shortname.data = user.shortname
        form.nickname.data = user.nickname
    return render_template('edit_user.html', title='Edit User', form=form)


@app.route('/edit_user_password', methods=['GET', 'POST'])
#@app.route('/user/<user_id>/edit', methods=['GET', 'POST'])
@login_required
def route_edit_password():
    form = EditPasswordForm()
    user = current_user
    #user = User.query.filter_by(id=user_id).first_or_404()
    if form.validate_on_submit():
        tasks.update_password(
            user=user,
            password=form.password.data,
        )
        flash(f'Password of user {user} updated')
        return redirect(url_for('user', user_id=user.id))
    return render_template('edit_user_password.html', title='Moneyball', form=form)

@app.route('/match/<match_id>/approve', methods=['POST'])
@login_required
def route_approve_match(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    msg = tasks.approve_match(match, approver=current_user)
    flash(msg)
    return redirect(url_for('index'))

@app.route('/user/<user_id>/approval_pending')
@login_required
def route_approval_pending(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    matches = user.matches
    matches_pending_user_approval = []
    for m in matches:
        if user.can_approve_match(m):
            matches_pending_user_approval.append(m)

    return render_template('approval_pending.html', matches=matches_pending_user_approval)

@app.route('/.well-known/change-password')
def route_well_known_change_password():
    return redirect(url_for('route_edit_password'))