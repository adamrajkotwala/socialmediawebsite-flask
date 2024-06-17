import functools

import random

import string

import re

from flask import Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from datetime import datetime

from .functions import *

from flask import Flask

from flask_mail import Mail, Message 

app = Flask(__name__) 


# Configure Flask-Mail settings 
app.config['MAIL_SERVER'] = "10.200.146.27" 
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_TLS'] = True 
app.config['MAIL_USE_SSL'] = False 
app.config['MAIL_USERNAME'] = None 
app.config['MAIL_PASSWORD'] = None 
app.config['MAIL_DEFAULT_SENDER'] = 'default-sender@wv.gov' 

mail = Mail(app) 

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        password_con = request.form['password_con']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        birthday_str = request.form['birthday']

        error = None

        try:
            birthday = datetime.strptime(birthday_str, '%Y-%m-%d').date()
        except ValueError:
            error = "Invalid date format. Please use YYYY-MM-DD."

        db = get_db()

        if not email:
            error = 'Email is required.'
        elif not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif len(password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif not re.search(r'[A-Z]', password):
            error = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', password):
            error = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'[0-9]', password):
            error = 'Password must contain at least one digit.'
        elif not password_con:
            error = 'Password Confirmation is required.'
        elif password != password_con:
            error = 'Passwords do not match.'
        elif not first_name:
            error = "First name is required."
        elif not last_name:
            error = "Last name is required."
        elif not birthday_str:
            error = "Birthday is required."

        if error is None:
            existing_user = db.execute(
                'SELECT id FROM user WHERE email = ? OR username = ?',
                (email, username)
            ).fetchone()

            if existing_user:
                error = f"User {username} or email {email} is already registered."
            else:
                code = ''.join(random.choices(string.digits, k=6))
                return redirect(url_for('auth.verify', email=email, username=username, password=password, first_name=first_name, last_name=last_name, birthday=birthday, code=code))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/verify', methods=('GET', 'POST'))
def verify():
    email = request.args.get('email')
    code = '123456'#request.args.get('code')
    print(code)
    msg = Message( 
        subject="Greenbook Verification Code",
        recipients=[email], 
        body=code
        ) 
    mail.send(msg)
    if request.method == 'POST':

        username = request.args.get('username')
        password = request.args.get('password')
        first_name = request.args.get('first_name')
        last_name = request.args.get('last_name')
        birthday = request.args.get('birthday')

        input_code = request.form['input_code']

        if code == input_code:
            db = get_db()
            db.execute(
                "INSERT INTO user (email, username, password, first_name, last_name, birthday) VALUES (?, ?, ?, ?, ?, ?)",
                (email, username, generate_password_hash(password), first_name, last_name, birthday),
            )
            db.commit()
            return redirect(url_for('auth.login'))
        else:
            error = 'Code Invalid'
            flash(error)

    return render_template('auth/verify.html')

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
        elif len(new_password) < 8:
            error = 'Password must be at least 8 characters long.'
        elif not re.search(r'[A-Z]', new_password):
            error = 'Password must contain at least one uppercase letter.'
        elif not re.search(r'[a-z]', new_password):
            error = 'Password must contain at least one lowercase letter.'
        elif not re.search(r'[0-9]', new_password):
            error = 'Password must contain at least one digit.'
        elif not password_con:
            error = 'Password Confirmation is required.'
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