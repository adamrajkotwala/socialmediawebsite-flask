import functools

import random

import string

import re

import time

from flask import (
    Flask, Blueprint, flash, g, redirect, render_template, request, jsonify, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from werkzeug.exceptions import abort

from datetime import datetime

from flask import Flask

from flask_mail import Mail, Message 

app = Flask(__name__) 

bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@bp.route('/notifications')
def get_notifications():
    user_id = g.user['id']
    messages = get_messages(user_id)
    friend_requests = get_friend_requests(user_id)
    return render_template('notifications/notifications.html', messages=messages, friend_requests=friend_requests)

def get_messages(user_id):
    db = get_db()
    # Fetch messages from the notifications for the current user
    messages = db.execute(
        'SELECT m.id, sender_id, content, timestamp, is_read, username as sender_username'
        ' FROM message m JOIN user u ON m.sender_id = u.id'
        ' WHERE m.recipient_id = ?'
        ' ORDER BY timestamp DESC',
        (user_id,)
    ).fetchall()
    return messages

def get_friend_requests(user_id):
    db = get_db()
    friend_requests = db.execute(
        'SELECT r.*, u.username FROM relationship r '
        'JOIN user u ON r.first_user_id = u.id '
        'WHERE r.second_user_id = ? AND r.status = 1',
        (user_id,)
    ).fetchall()
    return friend_requests

@bp.route('/new_message', methods=('GET', 'POST'))
def new_message():
    user_id = g.user['id']
    messages = get_messages(user_id)
    if request.method == 'POST':
        recipient = request.form.get('recipient')
        content = request.form.get('content')

        db = get_db()
        db.execute(
            'INSERT INTO message (sender_id, recipient_id, content) VALUES (?, ?, ?)',
            (user_id, recipient, content)
        )
        db.commit()

        message_id = db.execute('SELECT last_insert_rowid()').fetchone()[0]

        # Insert the message into the recipient's inbox
        db.execute(
            'INSERT INTO inbox (user_id, message_id) VALUES (?, ?)',
            (recipient, message_id)
        )
        db.commit()

        return redirect(url_for('notifications.notifications'))
    else:
        return render_template('notifications/new_message.html', messages=messages)