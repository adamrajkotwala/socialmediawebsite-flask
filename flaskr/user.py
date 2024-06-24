from flask import (Blueprint, flash, g, redirect, render_template, request, url_for, send_file)

from werkzeug.exceptions import abort

from flaskr.auth import login_required

from flaskr.blog import has_liked_post

from flaskr.db import get_db

from PIL import Image, ImageDraw

from .functions import *

from datetime import datetime

import pytz

import io

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/user_profile', methods=('GET', 'POST'))
@login_required
def user_profile():
    db = get_db()
    user = db.execute(
            'SELECT * FROM user WHERE username = ?', (g.user['username'],)
        ).fetchone()
    user_posts = get_user_posts(user_id=user['id'])
    return render_template('user/user_profile.html', get_unseen_messages_count=get_unseen_messages_count, posts=user_posts, has_liked_post=has_liked_post, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)

def get_user_posts(user_id):
    """Retrieve all posts made by a specific user."""
    query = (
        'SELECT id, title, is_edited, body, created, author_id, like_count, comment_count'
        ' FROM post'
        ' WHERE author_id = ?'
    )
    posts = get_db().execute(query, (user_id,)).fetchall()
    return posts

@bp.route('/<string:username>/nonuser_profile', methods=('GET',))
@login_required
def nonuser_profile(username):
    db = get_db()
    other_user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
    
    if other_user is None:
        abort(404)

    posts = get_user_posts(user_id=other_user['id'])

    relationship = get_relationship(friend_id=other_user['id'])
    
    return render_template('user/nonuser_profile.html', get_unseen_messages_count=get_unseen_messages_count, user=other_user, posts=posts, relationship=relationship, has_pfp=has_pfp, has_liked_post=has_liked_post, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/<int:id>/edit_bio', methods=('GET', 'POST'))
@login_required
def edit_bio(id):
    if request.method == 'POST':
        user_bio = request.form['bio']
        user_id = id
        error = None
        if error == None:
            db = get_db()
            db.execute(
                "UPDATE user SET bio = ? WHERE id = ?",
                (user_bio, user_id),
            )
            db.commit()
            return redirect(url_for('user.user_profile'))     
    return render_template('user/edit_bio.html', get_unseen_messages_count=get_unseen_messages_count, edit_bio=edit_bio, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/<int:id>/profile_picture')
def profile_picture(id):
    db = get_db()
    row = db.execute("SELECT profile_picture FROM user WHERE id = ?", (id,)).fetchone()
    if row and row['profile_picture']:
        profile_picture = row['profile_picture']
        mimetype = get_mimetype(profile_picture)
        return send_file(io.BytesIO(profile_picture), mimetype=mimetype)
    return 'No profile picture found'

@bp.route('/crop_circle_50px/<int:id>')
def crop_circle_50px(id):
    db = get_db()
    row = db.execute("SELECT profile_picture FROM user WHERE id = ?", (id,)).fetchone()
    if row and row['profile_picture']:
        profile_picture = row['profile_picture']
        img = Image.open(io.BytesIO(profile_picture))
        img = img.resize((50, 50))

        mask = Image.new('L', (50, 50), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 50, 50), fill=255)

        img.putalpha(mask)

        img_byte_array = io.BytesIO()
        img.save(img_byte_array, format='PNG') 
        img_byte_array.seek(0)

        mimetype = 'image/png'
        return send_file(img_byte_array, mimetype=mimetype)
    return 'No profile picture found', 404

@bp.route('/crop_circle_30px/<int:id>')
def crop_circle_30px(id):
    db = get_db()
    row = db.execute("SELECT profile_picture FROM user WHERE id = ?", (id,)).fetchone()
    if row and row['profile_picture']:
        profile_picture = row['profile_picture']
        img = Image.open(io.BytesIO(profile_picture))
        
        img = img.resize((30, 30))

        mask = Image.new('L', (30, 30), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, 30, 30), fill=255)

        img.putalpha(mask)
        img_byte_array = io.BytesIO()
        img.save(img_byte_array, format='PNG')
        img_byte_array.seek(0)
        mimetype = 'image/png'
        return send_file(img_byte_array, mimetype=mimetype)
    else:
        return 'No profile picture found', 404

def get_mimetype(image_data):
    if image_data.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    elif image_data.startswith(b'\xff\xd8\xff\xe0\x00\x10JFIF') or image_data.startswith(b'\xff\xd8\xff\xe1'):
        return 'image/jpeg'
    elif image_data.startswith(b'GIF87a') or image_data.startswith(b'GIF89a'):
        return 'image/gif'
    elif image_data.startswith(b'\x00\x00\x01\x00'):
        return 'image/vnd.microsoft.icon'
    else:
        return 'image/jpeg'  # Default to JPEG if type not detected

@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    return render_template('user/settings.html', get_unseen_messages_count=get_unseen_messages_count, get_unseen_notifications_count=get_unseen_notifications_count, has_pfp=has_pfp)

@bp.route('/<int:id>/delete_pfp', methods=('POST',))
@login_required
def delete_pfp(id):
    db = get_db()
    db.execute(
        "UPDATE user SET profile_picture = ? WHERE id = ?",
        (None, id),
    )
    db.commit()
    return redirect(url_for('user.settings'))

@bp.route('/<int:friend_id>/send_friend_request', methods=('POST',))
@login_required
def send_friend_request(friend_id):
    db = get_db()
    db.execute(
        'INSERT INTO relationship (first_user_id, second_user_id, status)'
        ' VALUES (?, ?, ?)',
        (g.user['id'], friend_id, 1)
    )
    db.commit()
    formatted_time = get_formatted_time('America/New_York')
    db.execute(
        'INSERT INTO notification (type, user_id, other_user_id, other_user_username, time) VALUES (?, ?, ?, ?, ?)',
        ("friend_request_received", friend_id, g.user['id'], g.user['username'], formatted_time)
    )
    db.commit()
    return f"<script>window.location = '{request.referrer}'</script>"

@bp.route('/<int:friend_id>/cancel_friend_request', methods=('POST',))
@login_required
def cancel_friend_request(friend_id):
    db = get_db()
    db.execute(
        'DELETE FROM relationship '
        'WHERE (first_user_id = ? AND second_user_id = ?) '
        'OR (first_user_id = ? AND second_user_id = ?)',
        (g.user['id'], friend_id, friend_id, g.user['id'])
    )
    db.commit()
    db.execute(
        'DELETE FROM notification WHERE type = ? AND user_id = ? AND other_user_id = ?',
        ("friend_request_received", friend_id, g.user['id'])
    )
    db.commit()
    return f"<script>window.location = '{request.referrer}'</script>"

@bp.route('/<int:friend_id>/accept_friend_request', methods=('POST',))
@login_required
def accept_friend_request(friend_id):
    db = get_db()
    friend = get_user(friend_id)
    db.execute(
        'UPDATE relationship SET status = 2 WHERE first_user_id = ? AND second_user_id = ?',
        (friend_id, g.user['id'])
    )
    db.commit()
    db.execute(
        'UPDATE user SET friend_count = ? WHERE id = ?',
        (g.user['friend_count']+1, g.user['id'])
    )
    db.commit()
    db.execute(
        'UPDATE user SET friend_count = ? WHERE id = ?',
        (friend['friend_count']+1, friend_id)
    )
    db.commit()
    formatted_time = get_formatted_time('America/New_York')
    db.execute(
        'INSERT INTO notification (type, user_id, other_user_id, other_user_username, time) VALUES ( ?, ?, ?, ?, ?)',
        ("friend_request_accepted", friend_id, g.user['id'], g.user['username'], formatted_time)
    )
    db.commit()
    return f"<script>window.location = '{request.referrer}'</script>"

@bp.route('/<int:friend_id>/decline_friend_request', methods=('POST',))
@login_required
def decline_friend_request(friend_id):
    db = get_db()
    db.execute(
        'DELETE FROM relationship WHERE first_user_id = ? AND second_user_id = ? AND status = 1',
        (friend_id, g.user['id'])
    )
    db.commit()
    return f"<script>window.location = '{request.referrer}'</script>"

@bp.route('/<int:friend_id>/unfriend', methods=('POST',))
@login_required
def unfriend(friend_id):
    db = get_db()
    friend = get_user(friend_id)
    db.execute(
        'DELETE FROM relationship '
        'WHERE (first_user_id = ? AND second_user_id = ?) '
        'OR (first_user_id = ? AND second_user_id = ?)',
        (g.user['id'], friend_id, friend_id, g.user['id'])
    )
    db.commit()
    db.execute(
        'UPDATE user SET friend_count = ? WHERE id = ?',
        (g.user['friend_count']-1, g.user['id'])
    )
    db.commit()
    db.execute(
        'UPDATE user SET friend_count = ? WHERE id = ?',
        (friend['friend_count']-1, friend_id)
    )
    db.commit()
    db.execute(
        'DELETE FROM notification WHERE type = ? AND user_id = ? AND other_user_id = ?',
        ("friend_request_accepted", friend_id, g.user['id'])
    )
    db.commit()
    return f"<script>window.location = '{request.referrer}'</script>"

@login_required
def get_relationship(friend_id):
    db = get_db()
    user_id = g.user['id']
    relationship = db.execute(
        'SELECT * FROM relationship '
        'WHERE (first_user_id = ? AND second_user_id = ?) '
        'OR (first_user_id = ? AND second_user_id = ?)',
        (user_id, friend_id, friend_id, user_id)
    ).fetchone()
    return relationship

@bp.route('/<int:id>/view_friends', methods=('GET',))
@login_required
def view_friends(id):
    db = get_db()
    user = get_user(id)

    friends = db.execute(
        'SELECT u.id, u.username '
        'FROM user u '
        'JOIN relationship r ON (u.id = r.first_user_id OR u.id = r.second_user_id) '
        'WHERE (r.first_user_id = ? OR r.second_user_id = ?) AND r.status = 2 '
        'AND u.id != ?',
        (id, id, id)
    ).fetchall()

    error = None

    if user['friend_count'] == 0:
        error = "No friends"
        
    if error is not None:
        flash(error)
        return f"<script>window.location = '{request.referrer}'</script>"
    else:
        return render_template('user/view_friends.html', get_unseen_messages_count=get_unseen_messages_count, friends=friends, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)
    
@bp.route('/search', methods=('GET',))
@login_required
def search():
    query = request.args.get('query', '')

    if query:
        db = get_db()
        results = db.execute(
            "SELECT id, username, first_name, last_name "
            "FROM user "
            "WHERE username LIKE ? OR first_name LIKE ? OR last_name LIKE ?",
            ('%' + query + '%', '%' + query + '%', '%' + query + '%')
        ).fetchall()
    else:
        results = []

    return render_template('user/search.html', get_unseen_messages_count=get_unseen_messages_count, results=results, has_pfp=has_pfp,  get_unseen_notifications_count=get_unseen_notifications_count)
