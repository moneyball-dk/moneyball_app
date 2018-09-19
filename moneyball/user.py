
from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)
from werkzeug.exceptions import abort

from moneyball.auth import login_required
from moneyball.db import get_db

bp = Blueprint('user', __name__)



@bp.route('/user/')
def index():
    db = get_db()
    users = db.execute(
        f'SELECT id, username FROM user'
    ).fetchall()
    return render_template('user/index.html', users=users)

@bp.route('/user/<userid>')
def userpage(userid):
    db = get_db()
    user = db.execute(
        f'SELECT id, username FROM user WHERE id = {userid}'
    ).fetchone()
    stats = get_stats(userid)
    return render_template('user/userpage.html', user=user, stats=stats)

def get_stats(userid):
    db = get_db()
    m_w1 = db.execute(
        f'SELECT id FROM match WHERE winner_1_id = {userid}'
    ).fetchall()
    m_w2 = db.execute(
        f'SELECT id FROM match WHERE winner_2_id = {userid}'
    ).fetchall()
    m_l1 = db.execute(
        f'SELECT id FROM match WHERE loser_1_id = {userid}'
    ).fetchall()
    m_l2 = db.execute(
        f'SELECT id FROM match WHERE loser_2_id = {userid}'
    ).fetchall()

    elo = db.execute(
        'SELECT * FROM rating where user_id = ? ORDER BY update_date', (userid,)
    ).fetchone()
    try:
        elo = elo['elo']
    except:
        elo = None


    wins = len(m_w1) + len(m_w2)
    losses = len(m_l1) + len(m_l2)
    return wins, losses, elo