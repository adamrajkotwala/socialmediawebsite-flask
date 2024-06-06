from flask import Flask, render_template, request, redirect, url_for, send_from_directory, Blueprint, flash, g

import os

from werkzeug.exceptions import abort

import sqlite3

from flaskr.auth import login_required

from flaskr.db import get_db

from PIL import Image

import io

app = Flask(__name__)

bp = Blueprint('uploads', __name__)

from flask import Flask

@bp.route('/upload', methods=('POST',))
@login_required
def upload():

    type = request.form.get('type')
    file = request.files['file']

    error = None

    if not file:
        error = 'Image is required.'

    if error is not None:
        flash(error)
    else:
        if type == 'profile_picture':
            cropped_image_data = crop_square(file.read())
            db = get_db()
            db.execute("UPDATE user SET profile_picture = ? WHERE id = ?", (cropped_image_data, g.user['id']))
            db.commit()
            return f"<script>window.location = '{request.referrer}'</script>"
        
def crop_square(image_data):
    img = Image.open(io.BytesIO(image_data))

    width, height = img.size
    new_size = min(width, height)
    left = (width - new_size) / 2
    top = (height - new_size) / 2
    right = (width + new_size) / 2
    bottom = (height + new_size) / 2
    img = img.crop((left, top, right, bottom))

    img = img.resize((200, 200))

    img_byte_array = io.BytesIO()
    img.save(img_byte_array, format='JPEG')
    img_byte_array = img_byte_array.getvalue()

    return img_byte_array
