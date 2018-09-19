from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from moneyball.auth import login_required
from moneyball.db import get_db

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


        if not winner1:
            error = 'At least one winner required'
        
        elif not loser1:
            error = 'At least one loser required'

        if winner_score <= loser_score:
            error = 'Winner score should be more than loser score'
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
