import functools

import random

import string

import time

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, jsonify, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from werkzeug.exceptions import abort

from flask_mail import Mail, Message

app = Flask(__name__)

app.config['MAIL_SERVER'] = '10.200.146.27'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'greenbookhelp@gmail.com'
app.config['MAIL_PASSWORD'] = 'Testing$'
app.config['MAIL_DEFAULT_SENDER'] = 'greenbookhelp@gmail.com'

mail = Mail(app)

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_con = request.form['password_con']
        db = get_db()
        error = None

        if not email:
            error = 'Email is required.'
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not password_con:
            error = 'Password Confirmation is required.'
        elif password != password_con:
            error = 'Passwords do not match.'

        if error is None:
            existing_user = db.execute(
                'SELECT id FROM user WHERE email = ? OR username = ?',
                (email, username)
            ).fetchone()

            if existing_user:
                error = f"User {username} or email {email} is already registered."
            else:
                return redirect(url_for('auth.verify', email=email, username=username, password=password))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        email = request.args.get('email')
        username = request.args.get('username')
        password = request.args.get('password')
        db = get_db()
                
        # Generate a random 6-digit code
        code = '123456' #''.join(random.choices(string.digits, k=6))
        #send_verification_email(email, code)
        input_code = request.form['input_code']

        # Store the code along with the user's email (you can use session or database)
        #session['verification_code'] = {'email': email, 'code': code, 'timestamp': time.time()}

        # Send the code via email
        #send_verification_email(email, code)

        if code == input_code:
            db.execute(
                "INSERT INTO user (email, username, password) VALUES (?, ?, ?)",
                (email, username, generate_password_hash(password)),
            )
            db.commit()
            return redirect(url_for('auth.login'))
        else:
            error = 'Code Invalid'
        
        flash(error)

    return render_template('auth/verify.html')

def send_verification_email(email, code):
    msg = Message(
    'Greenbook Verification Code',
    recipients=[email],
    body=code
  )
    Mail.send(msg)

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = get_db().execute(
            'SELECT * FROM user WHERE id = ?', (user_id,)
        ).fetchone()

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view

@bp.route('/<int:id>/change_password', methods=('GET', 'POST'))
@login_required
def change_password(id):
    if request.method == 'POST':
        new_password = request.form['new_password']
        password_con = request.form['password_con']
        error = None
        user_id = id

        if not new_password:
            error = 'Password is required.'
        elif not password_con:
            error = 'Password confirmation is required.'
        elif new_password != password_con:
            error = "Passwords do not match."

        if error is None:
            db = get_db()
            db.execute(
                "UPDATE user SET password = ? WHERE id = ?",
                (generate_password_hash(new_password), user_id),
            )
            db.commit()
            flash('Password succesfully changed.')
            return redirect(url_for('user.profile'))

        flash(error)

    return render_template('auth/change_password.html')


@bp.route('/delete', methods=('GET', 'POST'))
@login_required
def delete_acc():
    if request.method == 'POST':
        password = request.form['password']
        db = get_db()
        error = None
        user = db.execute(
            'SELECT * FROM user WHERE username = ?', (g.user['username'],)
        ).fetchone()
        if not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        if error is None:
            db.execute('DELETE FROM user WHERE username = ?', (g.user['username'],))
            db.commit()
            db.execute('DELETE FROM like WHERE user_id = ?', (g.user['id'],))
            db.commit()
            session.clear()
            return redirect(url_for('index'))
        
        flash(error)
                
    return render_template('auth/deleteacc.html')