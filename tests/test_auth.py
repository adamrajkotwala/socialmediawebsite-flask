import pytest
from flask import g, session
from flaskr.db import get_db


def test_register(client):
    assert client.get('/auth/register').status_code == 200
    response = client.post(
        '/auth/register', data={'email' : 'example@gmail.com', 'username': 'test', 'password': 'test', 'password_con': 'test','first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01'}
    )
    assert response.headers["Location"] == "/auth/verify"

    # # Test with missing username
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'password': 'test', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Username is required.' in response.data

    # # Test with invalid email
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'invalid_email', 'username': 'test', 'password': 'test', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Invalid email address.' in response.data

    # # Test with no email
    # response = client.post(
    #     '/auth/register',
    #     data={'username': 'test', 'password': 'test', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Email is required.' in response.data

    # # Test with password that is not long enough
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'short', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Password must be at least 8 characters long.' in response.data

    # # Test with password that does not contain uppercase letter
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'alllowercase', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Password must contain at least one uppercase letter.' in response.data

    # # Test with password that does not contain lowercase letter
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'ALLUPPERCASE', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Password must contain at least one lowercase letter.' in response.data

    # # Test with password that does not contain digit
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'NoDigits', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Password must contain at least one digit.' in response.data

    # # Test with password and password confirmation that do not match
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'password1', 'password_con': 'password2', 'first_name': 'John', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Passwords do not match.' in response.data

    # # Test with missing first name
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'test', 'last_name': 'Doe', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'First name is required.' in response.data

    # # Test with missing last name
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'test', 'first_name': 'John', 'birthday': '1990-01-01', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Last name is required.' in response.data

    # # Test with missing birthday
    # response = client.post(
    #     '/auth/register',
    #     data={'email': 'example@gmail.com', 'username': 'test', 'password': 'test', 'first_name': 'John', 'last_name': 'Doe', 'bio': 'This is a test bio', 'profile_picture': None, 'friend_count': 0}
    # )
    # assert b'Birthday is required.' in response.data


# @pytest.mark.parametrize(('username', 'password', 'message'), (
#     ('', '', b'Username is required.'),
#     ('a', '', b'Password is required.'),
#     ('test', 'test', b'already registered'),
# ))
# def test_register_validate_input(client, username, password, message):
#     response = client.post(
#         '/auth/register',
#         data={'username': username, 'password': password}
#     )
#     assert message in response.data

def test_login(client, auth):
    assert client.get('/auth/login').status_code == 200
    response = auth.login()
    assert response.headers["Location"] == "/"

    with client:
        client.get('/')
        assert session['user_id'] == 1
        assert g.user['username'] == 'test'


@pytest.mark.parametrize(('username', 'password', 'message'), (
    ('a', 'test', b'Incorrect username.'),
    ('test', 'a', b'Incorrect password.'),
))
def test_login_validate_input(auth, username, password, message):
    response = auth.login(username, password)
    assert message in response.data

def test_logout(client, auth):
    auth.login()

    with client:
        auth.logout()
        assert 'user_id' not in session