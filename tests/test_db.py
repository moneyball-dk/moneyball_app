import pytest

@pytest.fixture
def my_app():
    from app import app
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    return app

@pytest.fixture(scope='function')
def empty_db(my_app):
    from app import db
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()


@pytest.fixture(scope='function')
def filled_db(empty_db):
    from app.models import User
    from app.routes import make_new_match

    u1 = User(username='kasper')
    u2 = User(username='felipe')
    
    m1 = make_new_match(winners=[u1], losers=[u2], w_score=10, 
        l_score=9, importance=32) # Kasper wins
    m2 = make_new_match(winners=[u1], losers=[u2], w_score=10, 
        l_score=9, importance=16) # Kasper wins
    m3 = make_new_match(winners=[u2], losers=[u1], w_score=10, 
        l_score=9, importance=16) # Felipe Wins
    yield empty_db
    empty_db.session.remove()
    empty_db.drop_all()


def test_password_hashing():
    from app.models import User
    u = User(username='kasper')
    u.set_password('correct-horse')
    assert not u.check_password('zebra')
    assert u.check_password('correct-horse')

def test_create_match(empty_db):
    from app.models import User
    from app.routes import make_new_match

    u1 = User(username='kasper')
    u2 = User(username='felipe')
    
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
    assert u1.username == 'kasper'
    assert u2.username == 'felipe'

    assert len(u1.matches) == 3
    assert len(u1.won_matches) == 2


def test_matches(filled_db):
    from app.models import Match

    matches = Match.query.all()
    assert len(matches) == 3

def test_delete_match(filled_db):
    from app.models import Match, User
    from app.routes import delete_match

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
    
