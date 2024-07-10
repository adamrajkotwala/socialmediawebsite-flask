from flask import Blueprint, flash, g, redirect, render_template, request, url_for, session

from werkzeug.exceptions import abort

from flaskr.auth import login_required

from flaskr.db import get_db

from flask import Flask

from .functions import *

import pytz

bp = Blueprint('blog', __name__)

app = Flask(__name__)

@bp.route('/')
def index():
    db = get_db()
    posts = db.execute(
        'SELECT p.id, title, body, is_edited, created, created_stamp, author_id, username, like_count, comment_count'
        ' FROM post p JOIN user u ON p.author_id = u.id'
        ' ORDER BY created_stamp DESC'
    ).fetchall()
    return render_template('blog/index.html', posts=posts, has_liked_post=has_liked_post, has_pfp=has_pfp, get_unseen_messages_count=get_unseen_messages_count, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/create_post', methods=('GET', 'POST'))
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['body']
        formatted_time = get_formatted_time('America/New_York')

        error = None
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
            post = db.execute(
                'SELECT * FROM post WHERE id = (SELECT last_insert_rowid())'
            ).fetchone()
            return redirect(url_for('blog.view_post', id=post['id']))

    return render_template('blog/create_post.html', has_pfp=has_pfp, get_unseen_messages_count=get_unseen_messages_count, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/<int:id>/update_post', methods=('GET', 'POST'))
@login_required
def update_post(id):
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
            formatted_time = get_formatted_time('America/New_York')
            db = get_db()
            db.execute(
                'UPDATE post SET title = ?, body = ?, created = ?, is_edited = ?'
                ' WHERE id = ?',
                (title, body, formatted_time, 1, id)
            )
            db.commit()
            return redirect(url_for('blog.view_post', id=id))

    return render_template('blog/update_post.html', post=post, has_pfp=has_pfp, get_unseen_messages_count=get_unseen_messages_count, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/<int:id>/delete_post', methods=('POST',))
@login_required
def delete_post(id):
    get_post(id)
    db = get_db()
    db.execute('DELETE FROM post WHERE id = ?', (id,))
    db.commit()
    db.execute('DELETE FROM like WHERE post_id = ?', (id,))
    db.commit()
    return redirect(url_for('blog.index'))

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
            formatted_time = get_formatted_time('America/New_York')
            db = get_db()
            db.execute(
                'UPDATE comment SET body = ?, created = ?, is_edited = ?'
                ' WHERE id = ?',
                (body, formatted_time, 1, id)
            )
            db.commit()
            return redirect(url_for('blog.view_post', id=post_id))

    return render_template('blog/update_comment.html', post=post, get_unseen_messages_count=get_unseen_messages_count, comment=comment, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/<int:post_id>/<int:id>/delete_comment', methods=('POST',))
@login_required
def delete_comment(post_id, id):
    db = get_db()
    db.execute('DELETE FROM comment WHERE id = ?', (id,))
    db.commit()
    post = get_post(post_id, check_author=False)
    db.execute(
        'UPDATE post SET comment_count = ?'
        ' WHERE id = ?',
        (post['comment_count']-1, post['id'])
    )
    db.commit()
    db.execute(
        'DELETE FROM notification WHERE type = ? AND user_id = ? AND other_user_id = ? AND post_id = ?',
        ("comment", id, g.user['id'], post['id'])
    )
    db.commit()
    return redirect(url_for('blog.view_post', id=post_id))

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
        return render_template('blog/view_post.html', post=post, has_liked_post=has_liked_post, comments=comments, has_pfp=has_pfp, get_unseen_messages_count=get_unseen_messages_count, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/<int:id>/like_post', methods=('POST',))
@login_required
def like_post(id):
    post = get_post(id, check_author=False)
    scroll_position = session.get('scrollPosition')
    session.pop('scrollPosition', None)
    if has_liked_post(g.user['id'], id) != True:
        db = get_db()
        db.execute(
            'INSERT INTO like (user_id, post_id) VALUES (?, ?)',
            (g.user['id'], id)
        )
        db.commit() # commit like
        db.execute(
            'UPDATE post SET like_count = ?'
            ' WHERE id = ?',
            (post['like_count']+1, id)          # add 1 to like count
        )
        db.commit() 
        formatted_time = get_formatted_time('America/New_York')
        db.execute(
            'INSERT INTO notification (type, user_id, other_user_id, other_user_username, time, post_id) VALUES (?, ?, ?, ?, ?, ?)',
            ('like', post['author_id'], g.user['id'], g.user['username'], formatted_time, post['id'])
        )
        db.commit() # send notification to recipient
        return f"<script>window.location = '{request.referrer}?scroll_position={scroll_position}'</script>"
    else:
        db = get_db()
        db.execute(
            'DELETE FROM like WHERE user_id = ? AND post_id = ?', # delete like
            (g.user['id'], id)
        )
        db.commit()
        db.execute(
            'UPDATE post SET like_count = ?'
            ' WHERE id = ?',
            (post['like_count']-1, id) # subtract 1 from like count
        )
        db.commit()
        db.execute(
            'DELETE FROM notification WHERE type = ? AND user_id = ? AND other_user_id = ? AND post_id = ?',
            ("like", id, g.user['id'], post['id']) # remove notifictaion from recipient
        )
        db.commit()
        return f"<script>window.location = '{request.referrer}?scroll_position={scroll_position}'</script>"