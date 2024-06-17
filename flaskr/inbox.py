import functools

import random

import string

import re

from flask import Flask, Blueprint, flash, g, redirect, render_template, request, session, url_for

from werkzeug.security import check_password_hash, generate_password_hash

from flaskr.db import get_db

from flaskr.auth import login_required

from datetime import datetime

from flask import Flask

from flask_mail import Mail, Message

from .functions import *

app = Flask(__name__)

bp = Blueprint('inbox', __name__, url_prefix='/inbox')

@bp.route('/inbox', methods=('GET',))
@login_required
def inbox():
    conversations = get_conversations()
    return render_template('inbox/inbox.html', start_conversation=start_conversation, conversations=conversations, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/start_conversation', methods=('POST',))
@login_required
def start_conversation():
    recipient_username = request.form['recipient_username']
    # Get the user IDs for the current user and the recipient
    user_id = g.user['id']
    user_username = g.user['username']
    recipient_user = get_user_by_username(recipient_username)
    recipient_id = recipient_user['id']

    # Check if a conversation already exists between the users
    existing_conversation = get_conversation(user_id, recipient_id)
    if existing_conversation:
        # Redirect to the existing conversation
        return redirect(url_for('inbox.conversation', user_id=user_id, other_user_id=recipient_id))

    # Otherwise, create a new conversation row
    db = get_db()
    db.execute(
        "INSERT INTO conversation (first_user_id, first_user_username, second_user_id, second_user_username) VALUES (?, ?, ?, ?)",
        (user_id, user_username, recipient_id, recipient_username),
    )
    db.commit()

    # Redirect to the newly created conversation
    return redirect(url_for('inbox.conversation', user_id=user_id, other_user_id=recipient_id))


@login_required
def get_conversations():
    db = get_db()
    user_id = g.user['id']
    conversations = db.execute(
        'SELECT * FROM conversation '
        'WHERE first_user_id = ? OR second_user_id = ?',
        (user_id, user_id)
    ).fetchall()
    return conversations

@bp.route('<int:user_id>/<int:other_user_id>/conversation', methods=('GET', 'POST'))
@login_required
def conversation(user_id, other_user_id):
    conversation = get_conversation(user_id, other_user_id)
    if request.method == 'POST':
        message_content = request.form['message_content']
        other_user = get_user(other_user_id)
        formatted_time = get_formatted_time('America/New_York')
        db = get_db()
        db.execute(
            "INSERT INTO message (sender_id, sender_username, recipient_id, recipient_username, content, time) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, g.user['username'], other_user_id, other_user['username'], message_content, formatted_time),
        )
        db.commit()
        return f"<script>window.location = '{request.referrer}'</script>"
    else:
        return render_template('inbox/conversation.html', get_unseen_notifications_count=get_unseen_notifications_count, has_pfp=has_pfp, conversation=conversation, user_id=user_id, other_user_id=other_user_id)

@bp.route('/<int:user_id>/<int:other_user_id>/get_conversation', methods=('GET',))
def get_conversation(user_id, other_user_id):
    db = get_db()
    conversation = db.execute(
        'SELECT * FROM conversation '
        'WHERE first_user_id = ? AND second_user_id = ? '
        'OR first_user_id = ? AND second_user_id = ?',
        (user_id, other_user_id, other_user_id, user_id)
    ).fetchone()
    return conversation