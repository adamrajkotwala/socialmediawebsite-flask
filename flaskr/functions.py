# inlcudes functions that are used in more than one file to prevent circular import

from flask import Flask, Blueprint, g

from werkzeug.exceptions import abort

import pytz

from flaskr.db import get_db

from datetime import datetime

from flask import Flask

app = Flask(__name__) 

bp = Blueprint('functions', __name__, url_prefix='/functions')

def get_user(id):
    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE id = ?', (id,)
    ).fetchone()
    return user

def get_user_by_username(username):
    db = get_db()
    user = db.execute(
        'SELECT * FROM user WHERE username = ?', (username,)
    ).fetchone()
    return user

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, is_edited, created, created_stamp, author_id, username, like_count, comment_count'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

def has_liked_post(user_id, post_id):
    post = get_post(post_id, check_author=False)
    if post['like_count'] > 0:
        try:
            db = get_db()
            result = db.execute(
                'SELECT 1 FROM like WHERE user_id = ? AND post_id = ?',
                (user_id, post_id)
            ).fetchone()
            if result is not None:
                return True
            else:
                return False
        except:
            return False
    else:
        return False

def has_pfp(id):
    db = get_db()
    user = db.execute(
        'SELECT profile_picture FROM user WHERE id = ?',
        (id,)
    ).fetchone()
    if user and user['profile_picture'] is not None:
        return True
    else:
        return False
    
def get_notifications():
    user_id = g.user['id']
    db = get_db()
    notifications = db.execute(
        'SELECT * FROM notification n JOIN user u ON n.other_user_id = u.id'
        ' WHERE n.user_id = ?'
        ' ORDER BY n.timestamp DESC',
        (user_id,)
    ).fetchall()
    return notifications

def get_unseen_notifications_count(user_id):
    db =  get_db()
    unseen_notification_count = db.execute(
        'SELECT COUNT(*) FROM notification WHERE user_id = ? AND is_seen = 0 AND other_user_id != ?',
        (user_id, user_id)
    ).fetchone()[0]
    return unseen_notification_count

def get_unseen_messages_count(user_id):
    db =  get_db()
    unseen_message_count = db.execute(
        'SELECT COUNT(*) FROM message WHERE recipient_id = ? AND is_read = 0',
        (user_id,)
    ).fetchone()[0]
    return unseen_message_count

@bp.context_processor
def inject_notifications_count():
    try:
        unseen_notifications_count = get_unseen_notifications_count(g.user['id'])
    except:
        unseen_notifications_count = 0
    return dict(unseen_notifications_count=unseen_notifications_count)

@bp.context_processor
def inject_messages_count():
    try:
        unseen_messages_count = get_unseen_messages_count(g.user['id'])
    except:
        unseen_messages_count = 0
    return dict(unseen_messages_count=unseen_messages_count)

def get_formatted_time(timezoneStr):
    timezone = pytz.timezone(timezoneStr)
    current_time = datetime.now(timezone)
    formatted_time = current_time.strftime('%m/%d/%Y @ %I:%M %p')
    return formatted_time

def get_comments(id):
    """Retrieve all comments made by a specific user."""
    query = (
        'SELECT id, post_id, author_id, author_username, body, created, is_edited, like_count, comment_count'
        ' FROM comment'
        ' WHERE post_id = ?'
    )
    comments = get_db().execute(query, (id,)).fetchall()
    return comments

def add_comment(post, comment_body):
    formatted_time = get_formatted_time('America/New_York')
    db = get_db()
    db.execute(
        'INSERT INTO comment (body, author_id, post_id, author_username, created)'
        ' VALUES (?, ?, ?, ?, ?)',
        (comment_body, g.user['id'], post['id'], g.user['username'], formatted_time)
    )
    db.commit()
    db.execute(
        'UPDATE post SET comment_count = ?'
        ' WHERE id = ?',
        (post['comment_count']+1, post['id'])
    )
    db.commit()
    db.execute(
        'INSERT INTO notification (type, user_id, other_user_id, other_user_username, time, post_id) VALUES (?, ?, ?, ?, ?, ?)',
        ('comment', post['author_id'], g.user['id'], g.user['username'], formatted_time, post['id'])
    )
    db.commit()
    return

def get_comment(id, check_author=True):
    comment = get_db().execute(
        'SELECT p.id, is_edited, body, created, author_id, username, like_count, comment_count'
        ' FROM comment p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if comment is None:
        abort(404, f"comment id {id} doesn't exist.")

    if check_author and comment['author_id'] != g.user['id']:
        abort(403)

    return comment

def get_user_playlists(user_id):
    db = get_db()
    playlists = db.execute(
        'SELECT * FROM playlist WHERE user_id = ?',
        (user_id,)
    ).fetchall()
    return playlists
