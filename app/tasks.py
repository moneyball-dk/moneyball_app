from app import db
from app.models import User, Rating, Match, UserMatch, Company
from datetime import datetime
import trueskill as ts
from dateutil.tz import gettz
import numpy as np
tz = gettz('Europe/Copenhagen')

def create_user(shortname, nickname, password, company, is_admin = 0):
    sn_user = User.query.filter(User.shortname == shortname.upper()).first()
    nn_user = User.query.filter(User.nickname == nickname).first()
    if sn_user is not None:
        raise AssertionError('Someone has already used that shortname')
    if nn_user is not None:
        raise AssertionError('Someone has already used that nickname')

    user = User(
        shortname = shortname.upper(),
        nickname = nickname,
        company = company,
        is_admin = is_admin
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    init_ratings(user)
    return user

def init_ratings(user, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz=tz)
    r_elo = Rating(user=user, rating_type='elo', rating_value=1500,
        timestamp=timestamp)
    r_ts_m = Rating(user=user, rating_type='trueskill_mu',
        rating_value=25, timestamp=timestamp)
    r_ts_s = Rating(user=user, rating_type='trueskill_sigma',
        rating_value=8.333, timestamp=timestamp)
    r_gd = Rating(user=user, rating_type='goal_difference',
        rating_value=0, timestamp=timestamp)
    db.session.add_all([r_elo, r_ts_m, r_ts_s])
    db.session.commit()

def recalculate_ratings(after_time=None):
    if after_time is None:
        # Set first datetime to earliest possible time
        after_time = datetime.min
    users = User.query.all()
    timestamps = []
    for u in users:
        # Get the first timestamp on Rating for each User
        # To initialize first Rating at earliest record of the user.
        try:
            time = Rating.query \
                .filter(Rating.user_id == u.id) \
                .order_by(Rating.timestamp) \
                .first().timestamp
            time.replace(tz=tz)
            timestamps.append(time)
        except AttributeError:
            time = datetime.now(tz=tz)
            # if no rating exists
            init_ratings(u, time)
            timestamps.append(time)
    Rating.query.filter(Rating.timestamp >= after_time).delete()
    #db.session.query(Rating).delete()
    db.session.commit()
    for u, t in zip(users, timestamps):
        # If user is created after `after_time`, reinit that users ratings.
        if t >= after_time:
            init_ratings(u, t)

    matches = Match.query \
        .filter(Match.approved_winner == True) \
        .filter(Match.approved_loser == True) \
        .filter(Match.timestamp >= after_time) \
        .order_by(Match.timestamp).all()
    for match in matches:
        update_match_ratings(match)

def delete_match(match):
    timestamp = match.timestamp
    db.session.delete(match)
    db.session.commit()
    recalculate_ratings(after_time=timestamp)

def update_match_ratings(match):
    if not match.approved_winner or not match.approved_loser:
        # Don't update ratings, as match is not approved
        return False
    update_trueskill_by_match(match)
    update_elo_by_match(match)
    update_goal_difference_by_match(match)

def update_elo_by_match(match):
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

def get_match_elo_change(match):
    Qs = []
    # First, get all winning players, then all losing players
    for players in [match.winning_players, match.losing_players]:
        # Get the avg elo for each team seperately
        elos = [p.get_current_elo() for p in players]
        avg_elo = sum(elos) / len(elos)
        Q = 10 ** (avg_elo / 400)
        Qs.append(Q)
    Q_w, Q_l = Qs
    exp_win = Q_w / (Q_w + Q_l)
    change_w = match.importance * (1 - exp_win)
    return change_w

def update_trueskill_by_match(match):
    w_ratings = []
    l_ratings = []
    for p in match.winning_players:
        mu, sigma = p.get_current_trueskill()
        w_ratings.append(ts.Rating(mu, sigma))

    for p in match.losing_players:
        mu, sigma = p.get_current_trueskill()
        l_ratings.append(ts.Rating(mu, sigma))

    rating_groups = [w_ratings, l_ratings]
    new_ratings = ts.rate(rating_groups, ranks=[0,1])
    players = match.winning_players + match.losing_players
    new_ratings_flat = [item for sublist in new_ratings for item in sublist]
    for player, rating in zip(players, new_ratings_flat):
        r_m = Rating(
            user=player,
            match=match,
            rating_type='trueskill_mu',
            rating_value=rating.mu,
            timestamp=match.timestamp,
        )
        r_s = Rating(
            user=player,
            match=match,
            rating_type='trueskill_sigma',
            rating_value=rating.sigma,
            timestamp=match.timestamp,
        )
        db.session.add_all([r_m, r_s])
        db.session.commit()

def update_goal_difference_by_match(match):
    diff = match.winner_score - match.loser_score

    for p in match.winning_players:
        current_gd = p.get_current_goal_difference()
        r = Rating(user=p, match=match, timestamp=match.timestamp,
            rating_type='goal_difference', rating_value=current_gd + diff)
        db.session.add(r)
    for p in match.losing_players:
        current_gd = p.get_current_goal_difference()
        r = Rating(user=p, match=match, timestamp=match.timestamp,
            rating_type='goal_difference', rating_value=current_gd - diff)
        db.session.add(r)
    db.session.commit()

def approve_match(match, approver):
    if approver in match.winning_players:
        match.approved_winner = True
    elif approver in match.losing_players:
        match.approved_loser = True
    else:
        # User not playing
        return 'Cant approve match. You are not a player in this match'
    db.session.commit()
    recalculate_ratings(after_time=match.timestamp)
    return 'Match approved'

def make_new_match(winners, losers, w_score, l_score, importance,
    user_creating_match=None, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now(tz=tz)
    approved_winner, approved_loser = False, False
    if user_creating_match in winners:
        approved_winner = True
    elif user_creating_match in losers:
        approved_loser = True
    match = Match(
        timestamp = timestamp,
        winner_score=w_score,
        loser_score=l_score,
        importance=importance,
        approved_winner=approved_winner,
        approved_loser=approved_loser)
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


def update_user(user, shortname, nickname, company):
    user.shortname = shortname.upper()
    user.nickname = nickname
    user.company = company
    db.session.commit()
    return user

def update_password(user, password):
    if password is not None:
        user.set_password(password)
    db.session.commit()
    return user

def choose_best_matchup(players, rating_type='elo'):
    # Sort players according to rating
    players = sorted(players, key=lambda x: x.get_current_rating(rating_type=rating_type))
    # Return best match for 2, 3, and 4 players
    if len(players) == 2:
        # Trivial
        return [players[0]], [players[1]]
    elif len(players) == 3:
        # 2 worst against the best
        t1 = players[:2]
        t2 = players[-1:]
        return t1, t2
    elif len(players) == 4:
        # Best and worst together against the middle
        t1 = [players[0], players[3]]
        t2 = [players[1], players[2]]
        return t1, t2
    return players, None

def create_company(company_name: str) -> Company:
    same_name = Company.query.filter(Company.name == company_name).first()
    if same_name is not None:
        raise AssertionError('A company with that name already exists')

    company = Company(name=company_name)
    db.session.add(company)
    db.session.commit()
    return company

