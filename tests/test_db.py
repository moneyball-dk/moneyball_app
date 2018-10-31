import pytest


def test_password_hashing():
    from app.models import User
    u = User(shortname='kasper')
    u.set_password('correct-horse')
    assert not u.check_password('zebra')
    assert u.check_password('correct-horse')

def test_create_match(empty_db):
    from app.models import User
    from app.tasks import make_new_match

    u1 = User(shortname='kasper')
    u2 = User(shortname='felipe')
    
    m1 = make_new_match(winners=[u1], losers=[u2], w_score=10, 
        l_score=9, importance=32) # Kasper wins
    
    assert u1.matches == [m1]
    assert u1.won_matches == [m1]
    assert not u1.lost_matches == [m1]
    assert u1.won_matches == u2.lost_matches

    assert m1.players == [u1, u2]
    assert m1.winning_players == [u1]
    assert m1.losing_players == [u2]

def test_users(filled_db):
    from app.models import User
    users = User.query.all()
    
    assert len(users) == 2
    u1, u2 = users
    assert u1.shortname == 'kasper'
    assert u2.shortname == 'felipe'

    assert len(u1.matches) == 3
    assert len(u1.won_matches) == 2


def test_matches(filled_db):
    from app.models import Match

    matches = Match.query.all()
    assert len(matches) == 3
    m1, m2, m3 = matches

    assert m1.players == m2.players
    assert m2.winning_players != m2.losing_players


def test_delete_match(filled_db):
    from app.models import Match, User
    from app.tasks import delete_match

    matches = Match.query.all()
    assert len(matches) == 3

    u1, u2 = User.query.all()
    # u1 has won more than u2, so higher rating
    assert u1.get_current_elo() > u2.get_current_elo()

    # Delete all the matches u1 has won
    [delete_match(m) for m in u1.won_matches]
    assert u1.get_current_elo() < u2.get_current_elo()

    matches = Match.query.all()
    assert len(matches) == 1

    delete_match(matches[0])
    assert u1.get_current_elo() == u2.get_current_elo()
    assert Match.query.all() == []
    
def test_create_user(filled_db):
    from app.tasks import create_user

    u = create_user(
        'NU',
        'New User',
        'hunter2'
    )

    assert u.shortname == 'NU'
    assert u.password_hash != 'hunter2'