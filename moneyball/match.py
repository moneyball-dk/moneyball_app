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
        'SELECT id, winner_1_id, winner_2_id,'
        ' loser_1_id, loser_2_id, played_date'
        ' FROM match'
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
        error = None


        if not winner1:
            error = 'At least one winner required'
        
        elif not loser1:
            error = 'At least one loser required'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO match (winner_1_id, winner_2_id, loser_1_id, loser_2_id)'
                ' VALUES (?, ?, ?, ?)',
                (winner1, winner2, loser1, loser2)
            )
            db.commit()
            return redirect(url_for('match.index'))
    db = get_db()
    users = db.execute(
        'SELECT id, username FROM user ORDER BY username'
    ).fetchall()

    return render_template('match/create.html', users=users)
