from flask import Flask, flash, Blueprint, g, jsonify, redirect, request, url_for, session, render_template
import requests
import urllib.parse
from .functions import *
from datetime import datetime
from flaskr.db import get_db
from PIL import Image
import io
import base64

CLIENT_ID = 'd7e7a920c1d943c3a78d7cc0bcb4e85b'
CLIENT_SECRET = 'dac4ecb7dab94c43a2bf7f4c9ea96a67'
REDIRECT_URI = 'http://127.0.0.1:5000/api/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

app = Flask(__name__) 

bp = Blueprint('api', __name__, url_prefix='/api')

def user_row_to_dict(row):
    profile_picture_base64 = base64.b64encode(row['profile_picture']).decode('utf-8') if row['profile_picture'] else None

    return {
        'id': row['id'],
        'email': row['email'],
        'username': row['username'],
        'password': row['password'],
        'first_name': row['first_name'],
        'last_name': row['last_name'],
        'birthday': row['birthday'].isoformat() if row['birthday'] else None,
        'bio': row['bio'],
        'profile_picture': profile_picture_base64,
        'friend_count': row['friend_count']
    }

@bp.route('/get_user_json', methods=['GET'])
def get_user_json():
    db = get_db()
    user_obj = db.execute('SELECT * FROM user WHERE id = ?', (g.user['id'],)).fetchone()
    if user_obj:
        user_json = user_row_to_dict(user_obj)
    else:
        user_json = {}
    return jsonify(user_json)

@bp.route('/spotify_login')
def spotify_login():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Ensure the user is logged in

    db = get_db()
    user = db.execute('SELECT spotify_access_token, spotify_refresh_token, spotify_expires_at FROM user WHERE id = ?', (session['user_id'],)).fetchone()

    if user is None or not user['spotify_access_token'] or not user['spotify_refresh_token']:
        scope = 'user-read-private user-read-email'
        params = {
            'client_id': CLIENT_ID,
            'response_type': 'code',
            'scope': scope,
            'redirect_uri': REDIRECT_URI,
            'show_dialog': True
        }
        auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
        return redirect(auth_url)
    
    # Check if the token is expired
    if datetime.now().timestamp() > user['spotify_expires_at']:
        return redirect(url_for('api.refresh_token'))

    return redirect(url_for('api.get_playlists'))

@bp.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

        response = requests.post(TOKEN_URL, data=req_body)
        token_info = response.json()

        if 'access_token' in token_info:
            db = get_db()
            db.execute(
                'UPDATE user SET spotify_access_token = ?, spotify_refresh_token = ?, spotify_expires_at = ? WHERE id = ?',
                (token_info['access_token'], token_info['refresh_token'], datetime.now().timestamp() + token_info['expires_in'], g.user['id'])
            )
            db.commit()

            # Store tokens in session for immediate use
            session['access_token'] = token_info['access_token']
            session['refresh_token'] = token_info['refresh_token']
            session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

            return redirect(url_for('api.get_playlists'))
    
    return redirect(url_for('api.spotify_login'))

@bp.route('/playlists')
def get_playlists():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Redirect to login if user not logged in

    # Fetch user's Spotify playlists
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }
    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists_data = response.json().get('items', [])

    # Initialize a list to store playlist data to insert into the database
    playlists_to_insert = []

    # Iterate over each playlist from Spotify API response
    for playlist in playlists_data:
        playlist_id = playlist['id']
        playlist_name = playlist['name']
        playlist_description = playlist['description']
        playlist_external_url = playlist['external_urls']['spotify']
        playlist_image_url = playlist['images'][0]['url'] if playlist['images'] else None
        playlist_total_tracks = playlist['tracks']['total']
        playlist_owner = playlist['owner']['display_name']

        image_bytes = None
        if playlist_image_url:
            response = requests.get(playlist_image_url)
            image = Image.open(io.BytesIO(response.content))
            image = image.resize((300, 300))  # Resize to 300x300 pixels, adjust as needed
            buffered = io.BytesIO()
            image.save(buffered, format="JPEG")
            image_bytes = buffered.getvalue()

        # Prepare data for insertion into database
        playlist_entry = {
            'user_id': session['user_id'],
            'spotify_id': playlist_id,
            'name': playlist_name,
            'description': playlist_description,
            'external_url': playlist_external_url,
            'image': image_bytes,  # Store the image as bytes
            'total_tracks': playlist_total_tracks,
            'owner': playlist_owner
        }
        playlists_to_insert.append(playlist_entry)

    # Insert playlists into the database
    db = get_db()
    db.execute('DELETE FROM playlist WHERE user_id = ?', (session['user_id'],))
    db.commit()
    for playlist_entry in playlists_to_insert:

        existing_playlist = db.execute(
            'SELECT id FROM playlist WHERE user_id = ? AND spotify_id = ?',
            (session['user_id'], playlist_id)
        ).fetchone()

        if existing_playlist:

            db.execute(
                'UPDATE playlists SET name = ?, description = ?, external_url = ?, image = ?, total_tracks = ? WHERE id = ?',
                (playlist_entry['name'], playlist_entry['description'], playlist_entry['external_url'], playlist_entry['image'], playlist_entry['total_tracks'], existing_playlist['id'])
            )

        else:

            db.execute(
                'INSERT INTO playlist (user_id, spotify_id, name, description, external_url, image, total_tracks, owner) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                (playlist_entry['user_id'], playlist_entry['spotify_id'], playlist_entry['name'],
                playlist_entry['description'], playlist_entry['external_url'], playlist_entry['image'],
                playlist_entry['total_tracks'], playlist_entry['owner'])
            )

    db.execute(
        "UPDATE user SET is_spotify_connected = 1 WHERE id = ?",
        (session['user_id'],),
    )

    db.commit()

    # Retrieve playlists from the database
    playlists = get_user_playlists(session['user_id'])

    flash('Spotify Connected')

    return render_template('user/user_profile.html', playlists=playlists, get_unseen_messages_count=get_unseen_messages_count, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/disconnect_spotify')
def disconnect_spotify():
    db = get_db()
    db.execute(
        'DELETE FROM playlist '
        'WHERE user_id = ?',
        (g.user['id'],)
    )
    db.commit()

    db.execute(
        "UPDATE user SET is_spotify_connected = 0, spotify_access_token = NULL, spotify_refresh_token= NULL, spotify_expires_at = NULL WHERE id = ?",
        (g.user['id'],),
    )
    db.commit()
    playlists = get_user_playlists(session['user_id'])

    flash('Spotify Disconnected')

    return render_template('user/user_profile.html', playlists=playlists, get_unseen_messages_count=get_unseen_messages_count, has_pfp=has_pfp, get_unseen_notifications_count=get_unseen_notifications_count)

@bp.route('/refresh_token')
def refresh_token():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))  # Ensure the user is logged in

    db = get_db()
    user = db.execute('SELECT spotify_refresh_token FROM user WHERE id = ?', (session['user_id'],)).fetchone()

    if user is None:
        return redirect(url_for('api.spotify_login'))  # User does not have Spotify tokens

    req_body = {
        'grant_type': 'refresh_token',
        'refresh_token': user['spotify_refresh_token'],
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }

    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    if 'access_token' in new_token_info:
        db.execute(
            'UPDATE user SET spotify_access_token = ?, spotify_expires_at = ? WHERE id = ?',
            (new_token_info['access_token'], datetime.now().timestamp() + new_token_info['expires_in'], session['user_id'])
        )
        db.commit()

        # Store tokens in session for immediate use
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        return redirect(url_for('api.get_playlists'))

    return redirect(url_for('api.spotify_login'))
