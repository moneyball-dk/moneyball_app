import pytest 


@pytest.fixture(scope='module')
def test_client():
    from app import app
    
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    testing_client = app.test_client()
    ctx = app.app_context()
    ctx.push()
    yield testing_client
    ctx.pop()

@pytest.fixture(scope='function')
def empty_db(test_client):
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