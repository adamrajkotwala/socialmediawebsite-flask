from flask import (
    Blueprint, flash, g, redirect, render_template, request, url_for
)

from werkzeug.exceptions import abort

from flaskr.auth import login_required

from flaskr.db import get_db

from datetime import datetime

import pytz

bp = Blueprint('blog', __name__)

from flask import Flask

app = Flask(__name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, created, created_stamp, author_id, username, like_count, comment_count'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created_stamp DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts, has_liked_post=has_liked_post, has_pfp=has_pfp)

@bp.route('/create', methods=('GET', 'POST'))
@login_required
def create():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        timezone = pytz.timezone('America/New_York')

        current_time = datetime.now(timezone)

        formatted_time = current_time.strftime('%m/%d/%Y %I:%M %p')

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'INSERT INTO post (title, body, author_id, created)'
                ' VALUES (?, ?, ?, ?)',
                (title, body, g.user['id'], formatted_time)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/create.html')

def get_post(id, check_author=True):
    post = get_db().execute(
        'SELECT p.id, title, body, created, created_stamp, author_id, username, like_count, comment_count'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if post is None:
        abort(404, f"Post id {id} doesn't exist.")

    if check_author and post['author_id'] != g.user['id']:
        abort(403)

    return post

@bp.route('/<int:id>/update', methods=('GET', 'POST'))
@login_required
def update(id):
    post = get_post(id)

    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        error = None

        if not title:
            error = 'Title is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?'
                ' WHERE id = ?',
                (title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))

    return render_template('blog/update.html', post=post)

@bp.route('/<int:id>/delete', methods=('POST',))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    db.execute('DELETE FROM like WHERE post_id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

def get_comments(id):
    """Retrieve all comments made by a specific user."""
    query = (
        'SELECT id, post_id, author_id, author_username, body, created, like_count, comment_count'
        ' FROM comment'
        ' WHERE post_id = ?'
    )
    comments = get_db().execute(query, (id,)).fetchall()
    return comments


def add_comment(post, comment_body):
    db = get_db()
    db.execute(
        'INSERT INTO comment (body, author_id, post_id, author_username)'
        ' VALUES (?, ?, ?, ?)',
        (comment_body, g.user['id'], post['id'], g.user['username'])
    )
    db.commit()
    db.execute(
        'UPDATE post SET comment_count = ?'
        ' WHERE id = ?',
        (post['comment_count']+1, post['id'])
    )
    db.commit()
    return

def get_comment(id, check_author=True):
    comment = get_db().execute(
        'SELECT p.id, body, created, author_id, username, like_count, comment_count'
        ' FROM comment p JOIN user u ON p.author_id = u.id'
        ' WHERE p.id = ?',
        (id,)
    ).fetchone()

    if comment is None:
        abort(404, f"comment id {id} doesn't exist.")

    if check_author and comment['author_id'] != g.user['id']:
        abort(403)

    return comment

@bp.route('/<int:post_id>/<int:id>/update_comment', methods=('GET', 'POST'))
@login_required
def update_comment(post_id, id):
    comment = get_comment(id)
    post = get_post(post_id, check_author=False)
    if request.method == 'POST':
        body = request.form['body']
        error = None

        if not body:
            error = 'Edit is required.'

        if error is not None:
            flash(error)
        else:
            db = get_db()
            db.execute(
                'UPDATE comment SET body = ?'
                ' WHERE id = ?',
                (body, id)
            )
            db.commit()
            return redirect(url_for('blog.view_post', id=post_id))

    return render_template('blog/update_comment.html', post=post, comment=comment)

@bp.route('/<int:post_id>/<int:id>/delete_comment', methods=('POST',))
@login_required
def delete_comment(post_id, id):
    # comment = get_comment(id)
    db = get_db()
    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()
    # db.execute('DELETE FROM like WHERE post_id = ?', (id,))
    # db.commit()
    post = get_post(post_id, check_author=False)
    db.execute(
        'UPDATE post SET comment_count = ?'
        ' WHERE id = ?',
        (post['comment_count']-1, post['id'])
    )
    db.commit()
    posts = db.execute(
        'SELECT p.id, title, body, created, author_id, username, like_count, comment_count'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts, has_liked_post=has_liked_post)

@bp.route('/<int:id>/view_post', methods=('GET', 'POST'))
@login_required
def view_post(id):
    post = get_post(id, check_author=False)
    comments = get_comments(id)
    if request.method == 'POST':
        comment_body = request.form['comment']
        error = None
        if not comment_body:
            error = 'Comment is required.'
        if error is not None:
            flash(error)
        else:
            add_comment(post, comment_body)
        return f"<script>window.location = '{request.referrer}'</script>"
    else:
        return render_template('blog/view_post.html', post=post, has_liked_post=has_liked_post, comments=comments)

@bp.route('/<int:id>/like_post', methods=('POST',))
@login_required
def like_post(id):
    post = get_post(id, check_author=False)
    if has_liked_post(g.user['id'], id) != True:
        db = get_db()
        db.execute(
            'INSERT INTO like (user_id, post_id) VALUES (?, ?)',
            (g.user['id'], id)
        )
        db.commit()
        db.execute(
            'UPDATE post SET like_count = ?'
            ' WHERE id = ?',
            (post['like_count']+1, id)
        )
        db.commit()
        return f"<script>window.location = '{request.referrer}'</script>"
    else:
        db = get_db()
        db.execute(
            'DELETE FROM like WHERE user_id = ? AND post_id = ?',
            (g.user['id'], id)
        )
        db.execute(
            'UPDATE post SET like_count = ?'
            ' WHERE id = ?',
            (post['like_count']-1, id)
        )
        db.commit()
        return f"<script>window.location = '{request.referrer}'</script>"

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
    print(id)
    user = db.execute(
        'SELECT profile_picture FROM user WHERE id = ?',
        (id,)
    ).fetchone()
    if user and user['profile_picture'] is not None:
        return True
    else:
        return False