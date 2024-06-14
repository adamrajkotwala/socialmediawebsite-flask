from flask import Flask, request, Blueprint, flash, g

from flaskr.auth import login_required

from flaskr.db import get_db

from PIL import Image

import io

app = Flask(__name__)

bp = Blueprint('uploads', __name__)

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
        return f"<script>window.location = '{request.referrer}'</script>"
    else:
        if type == 'profile_picture':
            cropped_image_data = crop_square(file.read())
            db = get_db()
            db.execute("UPDATE user SET profile_picture = ? WHERE id = ?", (cropped_image_data, g.user['id']))
            db.commit()
            return f"<script>window.location = '{request.referrer}'</script>"
        
def crop_square(image_data):
    try:
        img = Image.open(io.BytesIO(image_data))
    except:
        flash('Image could not be uploaded')
        return None

    # Ensure the image is in RGB mode
    if img.mode == 'RGBA':
        # Create a white background image
        background = Image.new("RGB", img.size, (255, 255, 255))
        # Paste the RGBA image onto the background image
        background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
        img = background

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