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
    return render_template('inbox/inbox.html', start_conversation=start_conversation, conversations=conversations, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count, delete_conversation=delete_conversation)

@bp.route('/start_conversation', methods=('POST',))
@login_required
def start_conversation():
    recipient_username = request.form['recipient_username']
    # Get the user IDs for the current user and the recipient
    user_id = g.user['id']
    user_username = g.user['username']
    recipient_user = get_user_by_username(recipient_username)
    if recipient_user is None:
        flash("User Not Found")
        return f"<script>window.location = '{request.referrer}'</script>"
    
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

def get_messages(user_id, other_user_id):
    db = get_db()
    messages = db.execute(
        'SELECT * FROM message '
        'WHERE sender_id = ? AND recipient_id = ? '
        'OR sender_id = ? AND recipient_id = ?',
        (user_id, other_user_id, other_user_id, user_id)
    ).fetchall()
    return messages

@bp.route('<int:user_id>/<int:other_user_id>/conversation', methods=('GET', 'POST'))
@login_required
def conversation(user_id, other_user_id):
    conversation = get_conversation(user_id, other_user_id)
    messages = get_messages(user_id, other_user_id)
    other_user = get_user(other_user_id)
    if request.method == 'POST':
        message_content = request.form['message_content']
        formatted_time = get_formatted_time('America/New_York')
        db = get_db()
        cursor = db.execute(
            "INSERT INTO message (sender_id, sender_username, recipient_id, recipient_username, content, time) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, g.user['username'], other_user_id, other_user['username'], message_content, formatted_time),
        )
        db.commit()
        new_message_id = cursor.lastrowid
        db.execute(
            'UPDATE conversation SET message_count = ?, last_message_id = ?, last_sender_id = ?, last_sender_username = ?, last_message_content = ?, last_message_time = ?'
            ' WHERE id = ?',
            (conversation['message_count'] + 1, new_message_id, user_id, g.user['username'], message_content, formatted_time, conversation['id'])
        )
        db.commit()
        return f"<script>window.location = '{request.referrer}'</script>"
    else:
        return render_template('inbox/conversation.html', delete_conversation=delete_conversation, messages=messages, get_unseen_notifications_count=get_unseen_notifications_count, has_pfp=has_pfp, conversation=conversation, user_id=user_id, other_user=other_user)

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

@bp.route('/<int:user_id>/<int:other_user_id>/delete_conversation', methods=('POST',))
def delete_conversation(conversation):
    db = get_db()

    if conversation['message_count'] > 1:
        db.execute(
            'DELETE FROM message '
            'WHERE sender_id = ? AND recipient_id = ? '
            'OR sender_id = ? AND recipient_id = ?',
            (conversation['first_user_id'], conversation['second_user_id'], conversation['second_user_id'], conversation['first_user_id'])
        )
    db.commit()
    db.execute(
        'DELETE FROM conversation '
        'WHERE first_user_id = ? AND second_user_id = ? '
        'OR first_user_id = ? AND second_user_id = ?',
        (conversation['first_user_id'], conversation['second_user_id'], conversation['second_user_id'], conversation['first_user_id'])
    )
    db.commit()
    return f"<script>window.location = '{request.referrer}'</script>"