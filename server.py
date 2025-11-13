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
        f'https://api.spotify.com/v1/search?q={query}&type=track&limit=5&market=US',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if response.status_code != 200:
        return jsonify({'error': f'Spotify API error: {response.status_code}', 'details': response.text}), response.status_code
    
    return jsonify(response.json())

@app.route('/api/recommendations')
def get_recommendations():
    track_id = request.args.get('seed_tracks')
    if not track_id:
        return jsonify({'error': 'Track ID required'}), 400
    
    token = get_access_token()
    
    # Get track details and audio features
    track_response = requests.get(
        f'https://api.spotify.com/v1/tracks/{track_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if track_response.status_code != 200:
        return jsonify({'error': 'Track not found'}), 404
    
    track_data = track_response.json()
    artist_name = track_data['artists'][0]['name']
    album_name = track_data.get('album', {}).get('name', '')
    genres = []
    
    # Get artist info for genres
    artist_response = requests.get(
        f'https://api.spotify.com/v1/artists/{track_data["artists"][0]["id"]}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if artist_response.status_code == 200:
        artist_data = artist_response.json()
        genres = artist_data.get('genres', [])
    else:
        artist_data = {}
    
    recommendations = []
    existing_ids = {track_id}  # Exclude the original track
    
    # Strategy 1: Get related artists and their top tracks
    artist_id = track_data['artists'][0]['id']
    related_response = requests.get(
        f'https://api.spotify.com/v1/artists/{artist_id}/related-artists',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if related_response.status_code == 200:
        related_artists = related_response.json()['artists'][:8]  # More artists
        for artist in related_artists:
            top_tracks_response = requests.get(
                f'https://api.spotify.com/v1/artists/{artist["id"]}/top-tracks?market=US',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if top_tracks_response.status_code == 200:
                top_tracks = top_tracks_response.json()['tracks'][:3]  # More tracks per artist
                for track in top_tracks:
                    if track['id'] not in existing_ids and len(recommendations) < 15:
                        recommendations.append(track)
                        existing_ids.add(track['id'])
    
    # Strategy 2: Search by specific genre combinations
    if len(recommendations) < 12 and genres:
        for genre in genres[:3]:  # Try more genres
            # Multiple searches per genre
            searches = [
                f'genre:"{genre}" year:2020-2024',
                f'genre:"{genre}" year:2015-2019',
                f'genre:"{genre}"'
            ]
            
            for search_query in searches:
                if len(recommendations) >= 15:
                    break
                    
                genre_response = requests.get(
                    f'https://api.spotify.com/v1/search?q={search_query}&type=track&limit=20',
                    headers={'Authorization': f'Bearer {token}'}
                )
                
                if genre_response.status_code == 200:
                    tracks = genre_response.json()['tracks']['items']
                    sorted_tracks = sorted(tracks, key=lambda x: x.get('popularity', 0), reverse=True)
                    for track in sorted_tracks:
                        if (track['artists'][0]['name'] != artist_name and 
                            track['id'] not in existing_ids and 
                            len(recommendations) < 15):
                            recommendations.append(track)
                            existing_ids.add(track['id'])
    
    # Strategy 3: Album-based recommendations
    if len(recommendations) < 10:
        album_artists_response = requests.get(
            f'https://api.spotify.com/v1/albums/{track_data["album"]["id"]}/tracks',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if album_artists_response.status_code == 200:
            album_tracks = album_artists_response.json()['items']
            for track in album_tracks[:5]:  # More album tracks
                if track['id'] != track_id and track['id'] not in existing_ids:
                    full_track_response = requests.get(
                        f'https://api.spotify.com/v1/tracks/{track["id"]}',
                        headers={'Authorization': f'Bearer {token}'}
                    )
                    if full_track_response.status_code == 200:
                        recommendations.append(full_track_response.json())
                        existing_ids.add(track['id'])
    
    # Strategy 4: Fallback with broader searches
    if len(recommendations) < 8:
        fallback_searches = [
            f'artist:"{artist_name}"',  # More by same artist if needed
            f'year:{track_data.get("album", {}).get("release_date", "")[:4]}',
            'tag:new'
        ]
        
        for search in fallback_searches:
            if len(recommendations) >= 10:
                break
                
            fallback_response = requests.get(
                f'https://api.spotify.com/v1/search?q={search}&type=track&limit=15',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if fallback_response.status_code == 200:
                tracks = fallback_response.json()['tracks']['items']
                for track in tracks:
                    if track['id'] not in existing_ids and len(recommendations) < 10:
                        recommendations.append(track)
                        existing_ids.add(track['id'])
    
    return jsonify({'tracks': recommendations[:10]})

if __name__ == '__main__':
    app.run(debug=True, port=8000)