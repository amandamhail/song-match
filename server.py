from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import base64

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory('.', filename)

CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

def get_access_token():
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers={'Authorization': f'Basic {auth_base64}'},
        data={'grant_type': 'client_credentials'}
    )
    return response.json().get('access_token')

@app.route('/api/search')
def search_songs():
    query = request.args.get('q')
    if not query:
        return jsonify({'error': 'Query required'}), 400
    
    token = get_access_token()
    response = requests.get(
        f'https://api.spotify.com/v1/search?q={query}&type=track&limit=5',
        headers={'Authorization': f'Bearer {token}'}
    )
    return jsonify(response.json())

@app.route('/api/recommendations')
def get_recommendations():
    track_id = request.args.get('seed_tracks')
    if not track_id:
        return jsonify({'error': 'Track ID required'}), 400
    
    token = get_access_token()
    response = requests.get(
        f'https://api.spotify.com/v1/recommendations?seed_tracks={track_id}&limit=10',
        headers={'Authorization': f'Bearer {token}'}
    )
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True, port=8000)