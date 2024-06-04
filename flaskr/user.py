import functools

from flask import (Blueprint, flash, g, redirect, render_template, request, url_for)

from werkzeug.exceptions import abort

from flaskr.auth import login_required

from flaskr.blog import has_liked_post

from flaskr.db import get_db

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
        # user = get_user(id)
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
    print('Test Passed')
    return render_template('user/bio.html', bio=bio)

@bp.route('/settings', methods=('GET', 'POST'))
@login_required
def settings():
    return render_template('user/settings.html')