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

bp = Blueprint('inbox', __name__, url_prefix='/inbox')

@bp.route('/<int:id>/inbox')
def get_inbox(id):
    db = get_db()
    # Fetch messages from the inbox for the current user
    messages = db.execute(
        'SELECT m.id, sender_id, content, timestamp, is_read, username as sender_username'
        ' FROM message m JOIN user u ON m.sender_id = u.id'
        ' WHERE m.recipient_id = ?'
        ' ORDER BY timestamp DESC',
        (id,)
    ).fetchall()
    
    return render_template('inbox/inbox_user.html', messages=messages)