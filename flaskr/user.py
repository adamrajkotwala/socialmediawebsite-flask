import functools

from flask import (Blueprint, flash, g, redirect, render_template, request, url_for, send_file)

from werkzeug.exceptions import abort

from flaskr.auth import login_required

from flaskr.blog import has_liked_post

from flaskr.db import get_db

import io

bp = Blueprint('user', __name__, url_prefix='/user')

@bp.route('/profile', methods=('GET', 'POST'))
@login_required
def profile():
    db = get_db()
    user = db.execute(
            'SELECT * FROM user WHERE username = ?', (g.user['username'],)
        ).fetchone()
    posts = get_user_posts(user_id=user['id'])
    return render_template('user/profile.html', posts=posts, has_liked_post=has_liked_post)

def get_user_posts(user_id):
    """Retrieve all posts made by a specific user."""
    query = (
        'SELECT id, title, body, created, author_id, like_count, comment_count'
        ' FROM post'
        ' WHERE author_id = ?'
    )
    posts = get_db().execute(query, (user_id,)).fetchall()
    return posts

@bp.route('/<string:username>/profile_others', methods=('GET', 'POST'))
@login_required
def profile_others(username):
    # if request.method == 'POST':
    db = get_db()
    other_user = db.execute(
            'SELECT * FROM user WHERE username = ?', (username,)
        ).fetchone()
    
    if other_user is None:
        abort(404)

    posts = get_user_posts(user_id=other_user['id'])
    
    return render_template('user/profile_others.html', user=other_user, posts=posts, has_liked_post=has_liked_post)

@bp.route('/<int:id>/bio', methods=('GET', 'POST'))
@login_required
def bio(id):
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
            return redirect(url_for('user.profile'))     
    return render_template('user/bio.html', bio=bio)

@bp.route('/profile_picture/<int:id>')
def profile_picture(id):
    db = get_db()
    row = db.execute("SELECT profile_picture FROM user WHERE id = ?", (id,)).fetchone()
    if row and row['profile_picture']:
        profile_picture = row['profile_picture']
        mimetype = get_mimetype(profile_picture)
        return send_file(io.BytesIO(profile_picture), mimetype=mimetype)
    return 'No profile picture found'

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
    return render_template('user/settings.html')