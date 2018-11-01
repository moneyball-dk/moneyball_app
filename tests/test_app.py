import pytest

def test_index_page(test_client):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b'Moneyball' in response.data

def test_login(test_client, filled_db):
    response = test_client.get('/login')
    assert b'Sign in' in response.data
    assert b'Log out' not in response.data