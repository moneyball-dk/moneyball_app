from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from datetime import datetime

from app import app, db
from app.models import User, Match, UserMatch, Rating
from app.forms import LoginForm, RegistrationForm, CreateMatchForm, EditUserForm, ChooseLeaderboardSorting, EditPasswordForm, ChooseBestMatchupForm, SelectPlotResampleForm, CreateCompanyForm
from app.plots import plot_ratings
import time

from app import tasks

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index(sorting='elo'):
    form = ChooseLeaderboardSorting()
    sorting = form.sorting.data
    if current_user.is_authenticated:
        users = User.query.filter_by(company_id=current_user.company_id).all()
    else:
        users = User.query.all()
    users = [u for u in users if u.get_current_number_matches_approved() > 0]
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
            password=form.password.data,
            company=form.company.data,
        )
        if isinstance(user, User):
            flash('Congratulations! You are registered.')
        else:
            flash('Something went wrong')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<user_id>', methods=['GET', 'POST'])
def user(user_id):
    resample_interval = 'D'
    user = User.query.filter_by(id=user_id).first_or_404()
    form = SelectPlotResampleForm()
    if form.validate_on_submit():
        resample_interval = form.resample_interval.data
    b_div = plot_ratings(user.shortname, 'elo',
                         resample_interval=resample_interval)
    matches_pending = []
    for m in user.matches:
        if user.can_approve_match(m):
            matches_pending.append(m)

    return render_template('user.html', user=user, matches=user.matches,
                           b_div=b_div, title='User',
                           form=form,
                           matches_pending=matches_pending)

@app.route('/user/<user_id>/all_matches')
def route_user_all_matches(user_id):
    user = User.query.filter_by(id=user_id).first_or_404()
    return render_template('user_all_matches.html', user=user, matches=user.matches, title='All matches')

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
            timestamp=form.timestamp.data,
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
    if current_user.id == user_id or current_user.is_admin:
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
                company=form.company.data
            )
            flash(f'User {user} updated')
            return redirect(url_for('user', user_id=user.id))
        elif request.method == 'GET':
            form.shortname.data = user.shortname
            form.nickname.data = user.nickname
        return render_template('edit_user.html', title='Edit User', form=form)


@app.route('/edit_user_password', methods=['GET', 'POST'])
@login_required
def route_edit_password():
    user_id = current_user.id
    return route_edit_any_password(user_id)

@app.route('/user/<user_id>/edit_pass', methods=['GET', 'POST'])
@login_required
def route_edit_any_password(user_id):
    if current_user.id == user_id or current_user.is_admin:
        form = EditPasswordForm()
        user = User.query.filter_by(id=user_id).first_or_404()
        if form.validate_on_submit():
            tasks.update_password(
                user=user,
                password=form.password.data,
            )
            flash(f'Password of user {user} updated')
            return redirect(url_for('user', user_id=user.id))
        return render_template('edit_user_password.html', title='Moneyball', form=form)
    else:
        return False

@app.route('/match/<match_id>/approve', methods=['POST'])
@login_required
def route_approve_match(match_id):
    match = Match.query.filter_by(id=match_id).first_or_404()
    msg = tasks.approve_match(match, approver=current_user)
    flash(msg)
    return redirect(url_for('index'))

@app.route('/rules')
def rules():
    return render_template('rules.html')

@app.route('/.well-known/change-password')
def route_well_known_change_password():
    """
    Redirect to change password page.
    See https://github.com/WICG/change-password-url/blob/gh-pages/explainer.md
    """
    return redirect(url_for('route_edit_password'))


@app.route('/best_matchup', methods=['GET', 'POST'])
@login_required
def route_best_matchup():
    t1, t2 = None, None
    if not current_user.is_authenticated:
        flash('You have to login before creating a match.')
        return redirect(url_for('index'))
    form = ChooseBestMatchupForm()
    if form.validate_on_submit():
        players = form.players.data
        rating_type = form.rating_type.data
        t1, t2 = tasks.choose_best_matchup(players, rating_type)
    return render_template('choose_best_matchup.html',
                           title='Choose best matchup',
                           form=form, t1=t1, t2=t2)

@app.route('/create_company', methods=['GET', 'POST'])
@login_required
def create_company():
    if not current_user.is_authenticated:
        flash('You have to login before creating a match.')
        return redirect(url_for('index'))

    form = CreateCompanyForm()
    if form.validate_on_submit():
        company_name = form.name.data
        tasks.create_company(company_name)
    return render_template('add_company.html', title='Create company', form=form)