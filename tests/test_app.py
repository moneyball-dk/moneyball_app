import pytest
from flask import g, session

def test_index_page(test_client, filled_db):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Moneyball' in response.data

    # When we are not logged in we should not see leaderboard
    assert b'Highest ranking players' not in response.data

def test_login(test_client, filled_db):
    response = test_client.get('/login')
    assert response.status_code == 200
    assert b'Sign in' in response.data
    assert b'Log out' not in response.data

    # Log in
    response = login(test_client, 'kasper', '123')
    # Return to index
    assert response.status_code == 200
    assert b'Highest ranking players' in response.data
    # Flash success message
    assert b'successfully logged in' in response.data
    # Not on login page
    assert b'Sign In' not in response.data

    # Check that the correct user is logged in
    with test_client as client:
        client.get('/')
        assert session['user_id'] == '1'

    # Log in while already logged in
    response = test_client.get('/login')
    # Not on login page
    assert b'Sign In' not in response.data

    # Log out
    response = logout(test_client)
    assert response.status_code == 200
    assert b'User logged out' in response.data
    assert b'Home - Moneyball' in response.data
    assert b'Highest ranking players' not in response.data

    # Login wrong pass
    response = login(test_client, 'kasper', 'not-real-password')
    # Still on signin page
    assert response.status_code == 200
    assert b'Sign In' in response.data
    assert b'Invalid shortname or password' in response.data

    # login wrong user
    response = login(test_client, 'not-real-user', '123')
    assert response.status_code == 200
    assert b'Sign In' in response.data
    assert b'Invalid shortname or password' in response.data

def test_register(test_client, filled_db):
    # Register new user
    response = register_user(
        test_client, 
        shortname='NEWUSER',
        nickname='New guy',
        password='123',
        password2='123')

    # At loginpage
    assert response.status_code == 200
    assert b'You are registered' in response.data
    assert b'Sign In' in response.data

    # Login with new user
    response = login(test_client, 'newuser', '123')
    assert b'Highest ranking players' in response.data
    # Flash success message
    assert b'successfully logged in' in response.data

    # Register when already logged in 
    response = test_client.get('/register')
    # Not on register page
    assert b'Register' not in response.data
    

    # logout
    logout(test_client)

    # Register same shortname
    response = register_user(
        test_client, 
        shortname='NEWUSER',
        nickname='changed-nick',
        password='123',
        password2='123')
    assert response.status_code == 200
    assert b'Please use a different shortname' in response.data
    assert b'Register' in response.data

    # Register same nickname
    response = register_user(
        test_client, 
        shortname='changeshort',
        nickname='New guy',
        password='123',
        password2='123')
    assert response.status_code == 200
    assert b'Please use a different nickname' in response.data
    assert b'Register' in response.data

    # Register different passwords
    response = register_user(
        test_client, 
        shortname='changeshort',
        nickname='change-nick',
        password='123',
        password2='wrong-pass')
    assert response.status_code == 200
    assert b'must be equal to password' in response.data

def test_user_page(test_client, filled_db):
    # Test loading one user page
    response = test_client.get('/user/1')
    assert response.status_code == 200
    assert b'User' in response.data

    # Test 404 error for wrong user id
    response = test_client.get('/user/1000')
    assert response.status_code == 404

    # Test undefined winrate when no matches played
    from app.tasks import create_user
    u = create_user(shortname='NM', nickname='No matches', password='123', company=None)
    response = test_client.get(f'/user/{u.id}')
    assert response.status_code == 200
    assert b'Winrate: Undefined' in response.data

    # TODO: Is there any way to test plotting functions

def test_plot_candlestick(test_client, many_matches_db):
    # Just checking we are not crashing when running candlestick part of the plotting code
    response = test_client.get('/user/1')
    assert response.status_code == 200
    assert b'User' in response.data
    assert b'UserID: 1' in response.data


def test_match_page(test_client, filled_db):
    # Test match page when not logged in 
    response = test_client.get('/match/1')
    assert response.status_code == 200
    assert b'Match details' in response.data
    assert b'Winning players' in response.data
    assert b'KASPER' in response.data
    
    # Test match page when logged in
    login(test_client, 'kasper', '123')
    response = test_client.get('/match/1')
    assert b'Delete match?' in response.data

    # Test 404 page
    response = test_client.get('/match/1000')
    assert response.status_code == 404

def test_create_match_page(test_client, filled_db):
    from app.models import User
    u1, u2 = User.query.all()
    logout(test_client)
    response = register_match(
        test_client,
        [u1.id],
        [u2.id],
        10,
        6, 
        16
    )
    assert b'Please log in to access this page' in response.data
    assert response.status_code == 200

    login(test_client)
    response = register_match(
        test_client,
        [u1.id],
        [u2.id],
        10,
        6, 
        16
    )
    assert b'Match created' in response.data
    assert response.status_code == 200

@pytest.mark.parametrize(
    ('winner_ids', 'loser_ids', 'w_score', 'l_score', 'message'), (
    ([1], [2], 10, 7, b'Match created'),
    ([1], [1], 10, 7, b'Same user cannot be both winner and loser'),
    ([1], [2], 1, 10, b'Winning score must be greater than losing score')
))
def test_create_match_validate_input(test_client, filled_db,
    winner_ids, loser_ids, w_score, l_score, message):
    login(test_client)
    response = register_match( test_client, 
        winner_ids, loser_ids, w_score, l_score, 16)
    assert message in response.data


def login(client, shortname='kasper', password='123'):
    return client.post('/login', data=dict(
        shortname=shortname,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def register_user(client, shortname, nickname, password, password2):
    return client.post('/register', data=dict(
        shortname=shortname,
        nickname=nickname,
        password=password,
        password2=password2
    ), follow_redirects=True)

def register_match(client, winners, losers, w_score, l_score, importance):
    return client.post('/create_match',
        data=dict(
            winners=winners,
            losers=losers,
            winner_score=w_score,
            loser_score=l_score,
            importance=importance
        ), follow_redirects=True
    )

