from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from moneyball.auth import login_required
from moneyball.db import get_db
from collections import Counter

bp = Blueprint('match', __name__)

@bp.route('/')
def index():
    db = get_db()
    matches = db.execute(
        'SELECT m.id'
        ',m.winner_1_id'
        ',u1.username as winner_1_name'
        ',m.winner_2_id'
        ',u2.username as winner_2_name'
        ',m.loser_1_id'
        ',u3.username as loser_1_name'
        ',m.loser_2_id'
        ',u4.username as loser_2_name'
        ',m.played_date'
        ',m.winner_score'
        ',m.loser_score '
        ' FROM match m '
        'LEFT JOIN user u1 ON u1.id = m.winner_1_id '
        'LEFT JOIN user u2 ON u2.id = m.winner_2_id '
        'LEFT JOIN user u3 ON u3.id = m.loser_1_id '
        'LEFT JOIN user u4 ON u4.id = m.loser_2_id '
        ' ORDER BY played_date DESC'
    ).fetchall()

    return render_template('match/index.html', matches=matches)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        winner1 = request.form['winner1']
        winner2 = request.form['winner2']
        loser1 = request.form['loser1']
        loser2 = request.form['loser2']

        winner_score = request.form['winnerscore']
        loser_score = request.form['loserscore']
        error = None

        error = validate_players(winner1, winner2, loser1, loser2)

        if int(winner_score) <= int(loser_score):
            error = f'Winner score: {winner_score} should be more than loser score: {loser_score}'
        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO match (winner_1_id, winner_2_id, loser_1_id, loser_2_id, winner_score, loser_score)'
                ' VALUES (?, ?, ?, ?, ?, ?)',
                (winner1, winner2, loser1, loser2, winner_score, loser_score)
            )
            db.commit()
            # TODO: Update elo ratings after a match is played
            return redirect(url_for('match.index'))
    db = get_db()
    users = db.execute(
        'SELECT id, username FROM user ORDER BY username'
    ).fetchall()

    return render_template('match/create.html', users=users)


def validate_players(w1, w2, l1, l2):
    # At least one winner
    if not w1:
        return 'At least one winner is required'
    # At least one loser
    elif not l1:
        return 'At least one loser is required'
    
    # No repeated players
    players = [p for p in [w1, w2, l1, l2] if p is not None]
    count_players = Counter(players)
    for player, count in count_players.items():
        if count > 1:
            return 'Each player can only appear once.'
        
    return None

def update_elo(w1, w2, l1, l2, k=16):
    """
    Given pre-match elo ratings for winners and losers, 
    return the updated ratings
    """
    win_elos = [elo for elo in [w1, w2] if elo is not None]
    lose_elos = [elo for elo in [l1, l2] if elo is not None]
    win_avg = sum(win_elos) / len(win_elos)
    lose_avg = sum(lose_elos) / len(lose_elos)
    exp_win = None  # TODO: Fix me