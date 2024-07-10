from flask import Flask, Blueprint, flash, g, redirect, render_template, request, url_for, abort

from flaskr.db import get_db

from flaskr.auth import login_required

from flask import Flask

from .functions import *

app = Flask(__name__)

bp = Blueprint('inbox', __name__, url_prefix='/inbox')

@bp.route('/inbox_loader', methods=('GET',))
@login_required
def inbox_loader():
    conversations = get_conversations()
    for conversation in conversations:

        if (conversation['first_user_is_deleted'] == 1 and conversation['second_user_is_deleted'] == 1) or conversation['message_count'] == 0:
            delete_conversation(conversation['first_user_id'], conversation['second_user_id'])

        set_last_message(conversation, g.user['id'])

    f"<script>window.location = '{request.referrer}'</script>"
    return redirect(url_for('inbox.inbox', get_unseen_messages_count=get_unseen_messages_count, start_conversation=start_conversation, conversations=conversations, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count, delete_conversation=delete_conversation))

@bp.route('/inbox', methods=('GET',))
@login_required
def inbox():
    conversations = get_conversations()
    return render_template('inbox/inbox.html', get_unseen_messages_count=get_unseen_messages_count, start_conversation=start_conversation, conversations=conversations, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count, delete_conversation=delete_conversation)

@bp.route('/start_conversation', methods=('GET', 'POST'))
@login_required
def start_conversation():
    # Check for recipient_username in the URL query parameters first, then form data
    recipient_username = request.args.get('recipient_username') or request.form.get('recipient_username')

    # The rest of the function remains the same
    user_id = g.user['id']
    user_username = g.user['username']
    recipient_user = get_user_by_username(recipient_username)

    if recipient_user is None:
        flash("User Not Found")
        return f"<script>window.location = '{request.referrer}'</script>"

    if recipient_username == user_username:
        flash("You Cannot Message Yourself")
        return f"<script>window.location = '{request.referrer}'</script>"

    recipient_id = recipient_user['id']

    # Check if a conversation already exists between the users
    existing_conversation = get_conversation(user_id, recipient_id)
    if existing_conversation:
        # Redirect to the existing conversation
        return redirect(url_for('inbox.conversation', user_id=user_id, other_user_id=recipient_id))

    # Otherwise, create a new conversation row
    insert_conversation_row(user_id, user_username, recipient_id, recipient_username)

    # Redirect to the newly created conversation
    return redirect(url_for('inbox.conversation', user_id=user_id, other_user_id=recipient_id))

def insert_conversation_row(user_id, user_username, recipient_id, recipient_username):
    db = get_db()
    db.execute(
        "INSERT INTO conversation (first_user_id, first_user_username, second_user_id, second_user_username, message_count) VALUES (?, ?, ?, ?, 0)",
        (user_id, user_username, recipient_id, recipient_username),
    )
    db.commit()
    return

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
    if g.user['id'] != user_id and g.user['id'] != other_user_id:
        abort(403)

    conversation = get_conversation(user_id, other_user_id)
    other_user = get_user(other_user_id)
    messages = get_messages(user_id, other_user_id)

    if request.method == 'POST':
        message_content = request.form['message_content']
        last_message_preview = message_content[:20]+"..." if len(message_content) > 20 else message_content
        formatted_time = get_formatted_time('America/New_York')
        db = get_db()
        cursor = db.execute(
            "INSERT INTO message (sender_id, sender_username, recipient_id, recipient_username, content, time, conversation_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, g.user['username'], other_user_id, other_user['username'], message_content, formatted_time, conversation['id']),
        )
        db.commit()
        new_message_id = cursor.lastrowid
        db.execute(
            'UPDATE conversation SET message_count = ?, '
            'first_last_message_id = ?, first_last_sender_id = ?, first_last_sender_username = ?, first_last_message_preview = ?, first_last_message_time = ?, is_first_last_message_read = ?, '
            'second_last_message_id = ?, second_last_sender_id = ?, second_last_sender_username = ?, second_last_message_preview = ?, second_last_message_time = ?, is_second_last_message_read = ? '
            'WHERE id = ?',
            (
                conversation['message_count'] + 1,
                new_message_id, user_id, g.user['username'], last_message_preview, formatted_time, 0,
                new_message_id, user_id, g.user['username'], last_message_preview, formatted_time, 0,
                conversation['id']
            )
        )
        db.commit()

        if (conversation['first_user_is_deleted'] == 1) or (conversation['second_user_is_deleted'] == 1):
            db.execute(
                'UPDATE conversation SET first_user_is_deleted = 0, second_user_is_deleted = 0 '
                'WHERE id = ?',
                (conversation['id'],)
            )
            db.commit()

        return f"<script>window.location = '{request.referrer}'</script>"

    else:
        if conversation['message_count'] < 1:
            return render_template('inbox/conversation.html', get_unseen_messages_count=get_unseen_messages_count, delete_conversation=delete_conversation, messages=messages, get_unseen_notifications_count=get_unseen_notifications_count, has_pfp=has_pfp, conversation=conversation, user_id=user_id, other_user=other_user)

        for message in messages:
            if (message['sender_is_deleted'] == 1 and message['recipient_is_deleted'] == 1):
                delete_message(message['id'])

        # Update read status of the messages
        if conversation['first_last_sender_id'] != g.user['id'] and g.user['id'] == conversation['first_user_id']:
            db = get_db()
            db.execute(
                'UPDATE conversation SET is_first_last_message_read = 1 WHERE id = ?',
                (conversation['id'],)
            )
            db.commit()
            db.execute(
                'UPDATE message SET is_read = 1 WHERE sender_id = ? AND recipient_id = ? AND conversation_id = ?',
                (other_user_id, g.user['id'], conversation['id'])
            )
            db.commit()
        elif conversation['second_last_sender_id'] != g.user['id'] and g.user['id'] == conversation['second_user_id']:
            db = get_db()
            db.execute(
                'UPDATE conversation SET is_second_last_message_read = 1 WHERE id = ?',
                (conversation['id'],)
            )
            db.commit()
            db.execute(
                'UPDATE message SET is_read = 1 WHERE sender_id = ? AND recipient_id = ? AND conversation_id = ?',
                (other_user_id, g.user['id'], conversation['id'])
            )
            db.commit()

        return render_template('inbox/conversation.html', get_unseen_messages_count=get_unseen_messages_count, delete_conversation=delete_conversation, messages=messages, get_unseen_notifications_count=get_unseen_notifications_count, has_pfp=has_pfp, conversation=conversation, user_id=user_id, other_user=other_user)

def get_conversation(user_id, other_user_id):
    db = get_db()
    conversation = db.execute(
        'SELECT * FROM conversation '
        'WHERE first_user_id = ? AND second_user_id = ? '
        'OR first_user_id = ? AND second_user_id = ?',
        (user_id, other_user_id, other_user_id, user_id)
    ).fetchone()
    return conversation

# using login required causes an error with this function 
@bp.route('/<int:user_id>/<int:other_user_id>/get_conversation', methods=('GET',))
@login_required
def url_get_conversation(user_id, other_user_id):
    return get_conversation(user_id, other_user_id)

@bp.route('/<int:user_id>/<int:other_user_id>/delete_conversation', methods=('POST',))
@login_required
def delete_conversation(user_id, other_user_id):
    db = get_db()
    conversation = get_conversation(user_id, other_user_id)
    
    if conversation['message_count'] > 0:
        db.execute(
            'DELETE FROM message '
            'WHERE (sender_id = ? AND recipient_id = ?) '
            'OR (sender_id = ? AND recipient_id = ?)',
            (conversation['first_user_id'], conversation['second_user_id'], conversation['second_user_id'], conversation['first_user_id'])
        )
        db.commit()
    
    db.execute(
        'DELETE FROM conversation '
        'WHERE (first_user_id = ? AND second_user_id = ?) '
        'OR (first_user_id = ? AND second_user_id = ?)',
        (conversation['first_user_id'], conversation['second_user_id'], conversation['second_user_id'], conversation['first_user_id'])
    )
    db.commit()
    
    return f"<script>window.location = '{request.referrer}'</script>"

@bp.route('/<int:user_id>/<int:other_user_id>/soft_delete_conversation', methods=('POST',))
@login_required
def soft_delete_conversation(user_id, other_user_id):
    db = get_db()
    conversation = get_conversation(user_id, other_user_id)

    db.execute(
        'UPDATE message SET sender_is_deleted = 1'
        ' WHERE conversation_id = ? AND sender_id = ?',
        (conversation['id'], user_id)
    )
    db.commit()
    db.execute(
        'UPDATE message SET recipient_is_deleted = 1'
        ' WHERE conversation_id = ? AND recipient_id = ?',
        (conversation['id'], user_id)
    )
    db.commit()
    
    if user_id == conversation['first_user_id']:
        db.execute(
            'UPDATE conversation SET first_user_is_deleted = 1 '
            'WHERE id = ?',
            (conversation['id'],)
        )
        db.commit()
    else:
        db.execute(
            'UPDATE conversation SET second_user_is_deleted = 1 '
            'WHERE id = ?',
            (conversation['id'],)
        )
        db.commit()
    
    return f"<script>window.location = '{request.referrer}'</script>"

def get_messages(user_id, other_user_id):
    db = get_db()
    messages = db.execute(
        'SELECT * FROM message '
        'WHERE sender_id = ? AND recipient_id = ? '
        'OR sender_id = ? AND recipient_id = ? ' 
        'ORDER BY timestamp DESC',
        (user_id, other_user_id, other_user_id, user_id)
    ).fetchall()
    return messages

def get_message(message_id):
    db = get_db()
    messages = db.execute(
        'SELECT * FROM message '
        'WHERE id = ?',
        (message_id,)
    ).fetchone()
    return messages

def set_last_message(conversation, user_id):
    db = get_db()

    is_first_user = user_id == conversation['first_user_id']
    # Check for the most recent message not deleted by the user
    last_message = None
    if is_first_user:
        # Find the last message where the first user has not deleted it
        messages = db.execute(
            'SELECT * FROM message '
            'WHERE conversation_id = ? '
            'ORDER BY timestamp DESC',
            (conversation['id'],)
        ).fetchall()

        for message in messages:
            if (message['sender_id'] == user_id and message['sender_is_deleted'] == 0) or (message['recipient_id'] == user_id and message['recipient_is_deleted'] == 0):
                last_message = message
                break
    else:
        # Find the last message where the second user has not deleted it
        messages = db.execute(
            'SELECT * FROM message '
            'WHERE conversation_id = ? '
            'ORDER BY timestamp DESC',
            (conversation['id'],)
        ).fetchall()

        for message in messages:
            if (message['sender_id'] == user_id and message['sender_is_deleted'] == 0) or (message['recipient_id'] == user_id and message['recipient_is_deleted'] == 0):
                last_message = message
                break

    if last_message is not None:
        last_message_preview = last_message['content'][:20] + "..." if len(last_message['content']) > 20 else last_message['content']
        if is_first_user:
            db.execute(
                'UPDATE conversation SET '
                'first_last_message_id = ?, '
                'first_last_sender_id = ?, '
                'first_last_sender_username = ?, '
                'first_last_message_preview = ?, '
                'first_last_message_time = ?, '
                'first_last_message_timestamp = ?, '
                'is_first_last_message_read = ? '
                'WHERE id = ?',
                (
                    last_message['id'],
                    last_message['sender_id'],
                    last_message['sender_username'],
                    last_message_preview,
                    last_message['time'],
                    last_message['timestamp'],
                    last_message['is_read'],
                    conversation['id']
                )
            )
        else:
            db.execute(
                'UPDATE conversation SET '
                'second_last_message_id = ?, '
                'second_last_sender_id = ?, '
                'second_last_sender_username = ?, '
                'second_last_message_preview = ?, '
                'second_last_message_time = ?, '
                'second_last_message_timestamp = ?, '
                'is_second_last_message_read = ? '
                'WHERE id = ?',
                (
                    last_message['id'],
                    last_message['sender_id'],
                    last_message['sender_username'],
                    last_message_preview,
                    last_message['time'],
                    last_message['timestamp'],
                    last_message['is_read'],
                    conversation['id']
                )
            )
    else:
        if is_first_user:
            db.execute(
                'UPDATE conversation SET '
                'first_last_message_id = NULL, '
                'first_last_sender_id = NULL, '
                'first_last_sender_username = NULL, '
                'first_last_message_preview = ?, '
                'first_last_message_time = NULL, '
                'first_last_message_timestamp = NULL, '
                'is_first_last_message_read = 0 '
                'WHERE id = ?',
                (
                    "None",
                    conversation['id']
                )
            )
        else:
            db.execute(
                'UPDATE conversation SET '
                'second_last_message_id = NULL, '
                'second_last_sender_id = NULL, '
                'second_last_sender_username = NULL, '
                'second_last_message_preview = ?, '
                'second_last_message_time = NULL, '
                'second_last_message_timestamp = NULL, '
                'is_second_last_message_read = 0 '
                'WHERE id = ?',
                (
                    "None",
                    conversation['id']
                )
            )
    db.commit()
    return

def delete_message(message_id):
    message = get_message(message_id)
    conversation = get_conversation(message['sender_id'], message['recipient_id'])
    db = get_db()
    db.execute(
        'DELETE FROM message '
        'WHERE id = ?',
        (message_id,)
    )
    db.commit()
    db.execute(
        'UPDATE conversation SET message_count = ? '
        'WHERE id = ?',
        (conversation['message_count'] - 1, conversation['id'])
    )
    db.commit()
    return

@bp.route('/<int:message_id>/soft_delete_message', methods=('POST',))
@login_required
def soft_delete_message(message_id):
    db = get_db()
    message = get_message(message_id)
    conversation = get_conversation(message['sender_id'], message['recipient_id'])

    if g.user['id'] == message['sender_id']:
        db.execute(
            'UPDATE message SET sender_is_deleted = 1'
            ' WHERE id = ?',
            (message['id'],)
        )
        db.commit()
    else:
        db.execute(
            'UPDATE message SET recipient_is_deleted = 1'
            ' WHERE id = ?',
            (message['id'],)
        )
        db.commit()
    
    if message['sender_is_deleted'] == 1 and message['recipient_is_deleted'] == 1:

        db.execute(
            'DELETE FROM message '
            'WHERE id = ?',
            (message['id'],)
        )
        db.commit()

        db.execute(
            'UPDATE conversation SET message_count = ?'
            ' WHERE id = ?',
            (conversation['message_count'] - 1, conversation['id'])
        )
        db.commit()
    
    set_last_message(conversation, g.user['id'])
    
    return f"<script>window.location = '{request.referrer}'</script>"
