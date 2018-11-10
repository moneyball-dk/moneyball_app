import pytest
from flask import url_for

def test_index_page(test_client, filled_db):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Moneyball' in response.data

    # When we are not logged in we should not see leaderboard
    assert b'Highest ranking players' not in response.data

def test_login(test_client, filled_db):
    response = test_client.get('/login')
    assert b'Sign in' in response.data
    assert b'Log out' not in response.data

    # Log in
    response = login(test_client, 'kasper', '123')
    # Return to index
    assert b'Highest ranking players' in response.data
    # Flash success message
    assert b'successfully logged in' in response.data
    # Not on login page
    assert b'Sign In' not in response.data

    # Log out
    response = logout(test_client)
    assert b'User logged out' in response.data
    assert b'Home - Moneyball' in response.data
    assert b'Highest ranking players' not in response.data

    # Login wrong pass
    response = login(test_client, 'kasper', 'not-real-password')
    # Still on signin page
    assert b'Sign In' in response.data
    assert b'Invalid shortname or password' in response.data

    # login wrong user
    response = login(test_client, 'not-real-user', '123')
    assert b'Sign In' in response.data
    assert b'Invalid shortname or password' in response.data

def test_register(test_client, filled_db):
    # Register new user
    response = register(
        test_client, 
        shortname='NEWUSER',
        nickname='New guy',
        password='123',
        password2='123')

    # At loginpage
    assert b'You are registered' in response.data
    assert b'Sign In' in response.data

    # Login with new user
    response = login(test_client, 'newuser', '123')
    assert b'Highest ranking players' in response.data
    # Flash success message
    assert b'successfully logged in' in response.data

    # logout
    logout(test_client)

    # Register same shortname
    response = register(
        test_client, 
        shortname='NEWUSER',
        nickname='changed-nick',
        password='123',
        password2='123')
    assert b'Please use a different shortname' in response.data
    assert b'Register' in response.data

    # Register same nickname
    response = register(
        test_client, 
        shortname='changeshort',
        nickname='New guy',
        password='123',
        password2='123')
    assert b'Please use a different nickname' in response.data
    assert b'Register' in response.data

    # Register different passwords
    response = register(
        test_client, 
        shortname='changeshort',
        nickname='change-nick',
        password='123',
        password2='wrong-pass')
    assert b'must be equal to password' in response.data

def login(client, shortname, password):
    return client.post('/login', data=dict(
        shortname=shortname,
        password=password
    ), follow_redirects=True)

def logout(client):
    return client.get('/logout', follow_redirects=True)

def register(client, shortname, nickname, password, password2):
    return client.post('/register', data=dict(
        shortname=shortname,
        nickname=nickname,
        password=password,
        password2=password2
    ), follow_redirects=True)
