from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import base64
from dotenv import load_dotenv
import random

# Initialize AI models
sentiment_analyzer = None
text_generator = None

try:
    from transformers import pipeline, set_seed
    print("Loading AI models...")
    
    sentiment_analyzer = pipeline(
        "sentiment-analysis", 
        model="distilbert-base-uncased-finetuned-sst-2-english"
    )
    
    text_generator = pipeline(
        "text-generation", 
        model="EleutherAI/gpt-neo-125M",
        pad_token_id=50256
    )
    
    set_seed(42)
    print("AI models loaded successfully!")
    
except Exception as e:
    print(f"AI models failed to load: {e}")
    sentiment_analyzer = None
    text_generator = None

load_dotenv()

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

def generate_ai_recommendations_with_explanations(user_description, original_track, token):
    """Step 1: Generate exactly 9 song recommendations using AI"""
    if not text_generator:
        return []
    
    # Sanitize inputs to prevent errors
    orig_title = original_track['name'].replace('"', '').replace("'", '').strip()
    orig_artist = original_track['artists'][0]['name'].replace('"', '').replace("'", '').strip()
    user_description = user_description.replace('"', '').replace("'", '').strip()[:200]  # Limit length
    
    # Get audio features for context
    audio_features = get_audio_features(original_track['id'], token)
    features_text = ""
    
    if audio_features:
        tempo = int(audio_features.get('tempo', 120))
        energy = audio_features.get('energy', 0.5)
        valence = audio_features.get('valence', 0.5)
        danceability = audio_features.get('danceability', 0.5)
        
        energy_desc = "high energy" if energy > 0.6 else "low energy"
        mood_desc = "upbeat" if valence > 0.6 else "melancholic"
        dance_desc = "danceable" if danceability > 0.6 else "contemplative"
        
        features_text = f" '{orig_title}' is {energy_desc}, {mood_desc}, {dance_desc}, and has {tempo} BPM."
    
    try:
        # Skip AI generation and return empty list to use Spotify recommendations instead
        return []
        
        # Extract recommendations
        full_text = generated[0]['generated_text']
        ai_output = full_text.replace(prompt, '').strip()
        
        recommendations = []
        lines = ai_output.replace(',', '\n').split('\n')
        
        for line in lines:
            line = line.strip().lstrip('0123456789.-* ').strip()
            if len(line) > 8 and ('-' in line or 'by' in line.lower()):
                line = line.replace('"', '').replace("'", '').strip()
                if len(line) < 80:
                    recommendations.append(line)
                    if len(recommendations) >= 9:
                        break
        
        # If we don't have enough, generate more using different prompts
        while len(recommendations) < 9:
            # Try different prompt variations
            alt_prompts = [
                f"Songs similar to {orig_title} by {orig_artist}:",
                f"If you like {orig_title}, you'll love:",
                f"Music recommendations based on {orig_title}:",
                f"Artists similar to {orig_artist}:"
            ]
            
            for alt_prompt in alt_prompts:
                if len(recommendations) >= 9:
                    break
                    
                try:
                    alt_generated = text_generator(
                        alt_prompt,
                        max_new_tokens=100,
                        num_return_sequences=1,
                        temperature=0.9,
                        do_sample=True,
                        pad_token_id=50256,
                        eos_token_id=50256
                    )
                    
                    alt_text = alt_generated[0]['generated_text']
                    alt_output = alt_text.replace(alt_prompt, '').strip()
                    alt_lines = alt_output.replace(',', '\n').split('\n')
                    
                    for line in alt_lines:
                        line = line.strip().lstrip('0123456789.-* ').strip()
                        if len(line) > 8 and ('-' in line or 'by' in line.lower()):
                            line = line.replace('"', '').replace("'", '').strip()
                            if len(line) < 80 and line not in recommendations:
                                recommendations.append(line)
                                if len(recommendations) >= 9:
                                    break
                except:
                    continue
            
            # If still not enough, add generic fallbacks
            if len(recommendations) < 9:
                generic_songs = [
                    f"{orig_artist} - Similar Track 1",
                    f"{orig_artist} - Similar Track 2", 
                    f"Various Artists - Like {orig_title}",
                    f"Indie Rock - {energy_desc} Song",
                    f"Alternative - {mood_desc} Track"
                ]
                
                for song in generic_songs:
                    if len(recommendations) >= 9:
                        break
                    if song not in recommendations:
                        recommendations.append(song)
            
            break  # Prevent infinite loop
        
        return recommendations[:9]
        
    except Exception as e:
        print(f"AI recommendation error: {e}")
        # Return fallback songs if AI completely fails
        return [
            f"{orig_artist} - Similar Song 1",
            f"{orig_artist} - Similar Song 2",
            f"Alternative Rock - {energy_desc} Track",
            f"Indie Music - {mood_desc} Song",
            f"Similar Artists - Track 1",
            f"Similar Artists - Track 2",
            f"Genre Match - Song 1",
            f"Genre Match - Song 2",
            f"Recommended - Final Track"
        ]

def generate_individual_explanation(song_query, original_track, user_description, token=None):
    """Generate AI explanation for each specific song"""
    if not text_generator:
        return "Similar musical style."
    
    # Extract song info from query
    if ' - ' in song_query:
        parts = song_query.split(' - ', 1)
        rec_artist = parts[0].strip()
        rec_title = parts[1].strip()
    else:
        rec_artist = "Artist"
        rec_title = song_query
    
    orig_title = original_track['name']
    orig_artist = original_track['artists'][0]['name']
    
    try:
        # AI-only explanation generation
        prompt = f"{rec_title} by {rec_artist} is similar to {orig_title} by {orig_artist} because"
        
        generated = text_generator(
            prompt,
            max_new_tokens=20,
            num_return_sequences=1,
            temperature=0.8,
            do_sample=True,
            pad_token_id=50256,
            eos_token_id=50256
        )
        
        # Extract explanation
        full_text = generated[0]['generated_text']
        explanation = full_text.replace(prompt, '').strip()
        
        if explanation and len(explanation) > 5:
            # Clean up the explanation
            if '.' in explanation:
                explanation = explanation.split('.')[0]
            explanation = explanation.strip().rstrip(',').strip()
            
            if len(explanation) > 8:
                return f"{rec_title} by {rec_artist} is similar to {orig_title} by {orig_artist} because {explanation}."
        
        return f"Both tracks share similar musical characteristics."
        
    except Exception as e:
        print(f"AI explanation error: {e}")
        return f"Musical connection to {orig_title}."



def get_audio_features(track_id, token):
    """Get audio features for a track"""
    try:
        response = requests.get(
            f'https://api.spotify.com/v1/audio-features/{track_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Audio features error: {e}")
    return None

def generate_ai_song_recommendations(user_description, original_track, token):
    """Generate AI-powered song recommendations using audio features"""
    if not text_generator:
        return ['indie music', 'alternative songs', 'similar artists']
    
    try:
        orig_title = original_track['name']
        orig_artist = original_track['artists'][0]['name']
        
        # Get audio features for better recommendations
        audio_features = get_audio_features(original_track['id'], token)
        features_text = ""
        
        if audio_features:
            energy = "high energy" if audio_features.get('energy', 0.5) > 0.6 else "low energy"
            valence = "happy/positive" if audio_features.get('valence', 0.5) > 0.6 else "sad/melancholic"
            danceability = "danceable" if audio_features.get('danceability', 0.5) > 0.6 else "not danceable"
            tempo = audio_features.get('tempo', 120)
            tempo_desc = "fast" if tempo > 120 else "slow" if tempo < 90 else "medium"
            
            features_text = f" The song is {energy}, {valence}, {danceability}, and has a {tempo_desc} tempo ({int(tempo)} BPM)."
        
        # Enhanced AI prompt prioritizing musical similarity
        prompt = f"Find songs musically similar to '{orig_title}' by {orig_artist}.{features_text} Prioritize songs with matching genre, tempo, energy, and mood. User also mentioned: '{user_description}'. List 12 songs (artist - song title) with similar musical characteristics:"
        
        generated = text_generator(
            prompt,
            max_new_tokens=120,
            num_return_sequences=1,
            temperature=0.8,
            do_sample=True,
            pad_token_id=50256,
            eos_token_id=50256
        )
        
        # Extract and parse recommendations
        full_text = generated[0]['generated_text']
        ai_output = full_text.replace(prompt, '').strip()
        
        song_recommendations = []
        lines = ai_output.replace(',', '\n').split('\n')
        
        for line in lines:
            line = line.strip().lstrip('0123456789.-* ').strip()
            if len(line) > 8 and ('-' in line or 'by' in line.lower()):
                # Clean up common AI artifacts
                line = line.replace('"', '').replace("'", '').strip()
                if len(line) < 60:  # Reasonable song title length
                    song_recommendations.append(line)
        
        # Generate feature-based fallbacks using audio features
        if len(song_recommendations) < 8:
            fallbacks = generate_feature_based_queries(audio_features, user_description, orig_artist)
            song_recommendations.extend(fallbacks)
        
        return song_recommendations[:12]
        
    except Exception as e:
        print(f"AI recommendation error: {e}")
        return generate_fallback_queries(original_track, user_description)

def generate_feature_based_queries(audio_features, user_description, artist_name):
    """Generate search queries based on audio features"""
    queries = []
    
    if audio_features:
        # Energy-based queries
        if audio_features.get('energy', 0.5) > 0.7:
            queries.extend([f"{artist_name} energetic songs", "high energy indie rock"])
        else:
            queries.extend([f"{artist_name} mellow songs", "chill indie folk"])
        
        # Valence-based queries
        if audio_features.get('valence', 0.5) > 0.6:
            queries.extend(["upbeat alternative rock", "feel good indie"])
        else:
            queries.extend(["melancholic indie", "sad alternative songs"])
        
        # Tempo-based queries
        tempo = audio_features.get('tempo', 120)
        if tempo > 140:
            queries.append("fast paced indie")
        elif tempo < 80:
            queries.append("slow indie ballads")
    
    # Sentiment-based queries
    if sentiment_analyzer:
        try:
            sentiment = sentiment_analyzer(user_description)[0]
            if sentiment['label'] == 'POSITIVE':
                queries.extend(["similar uplifting songs", "positive indie music"])
            else:
                queries.extend(["emotional indie songs", "introspective music"])
        except:
            pass
    
    return queries[:6]

def generate_fallback_queries(original_track, user_description):
    """Generate fallback queries when AI fails"""
    artist_name = original_track['artists'][0]['name']
    return [
        f"{artist_name} similar artists",
        f"songs like {original_track['name']}",
        "indie alternative rock",
        "similar indie songs",
        "alternative music recommendations"
    ]

def generate_ai_search_queries(user_description, original_track):
    """Generate AI-powered search queries"""
    if not text_generator:
        return ['similar artists', 'indie music', 'alternative songs']
    
    try:
        # Use AI to generate search terms
        prompt = f"Someone loves a song because: '{user_description}'. What music search terms would find similar songs? Terms:"
        
        generated = text_generator(
            prompt,
            max_new_tokens=10,
            num_return_sequences=1,
            temperature=0.8,
            do_sample=True,
            pad_token_id=50256,
            eos_token_id=50256
        )
        
        queries = []
        for result in generated:
            text = result['generated_text'].replace(prompt, '').strip()
            # Extract meaningful search terms
            terms = [term.strip() for term in text.split(',')[:3] if len(term.strip()) > 2]
            queries.extend(terms)
        
        # Add sentiment-based queries using AI
        if sentiment_analyzer:
            sentiment = sentiment_analyzer(user_description)[0]
            if sentiment['label'] == 'NEGATIVE':
                queries.extend(['emotional songs', 'melancholy music'])
            elif sentiment['label'] == 'POSITIVE':
                queries.extend(['upbeat songs', 'feel good music'])
        
        # Clean and return unique queries
        clean_queries = [q for q in set(queries) if 3 < len(q) < 30]
        return clean_queries[:5] if clean_queries else ['similar artists', 'indie music']
        
    except Exception as e:
        print(f"Query generation error: {e}")
        return ['similar artists', 'indie music', 'alternative songs']

def ai_filter_recommendations(tracks, user_description, original_track, token=None):
    """AI-powered filtering prioritizing musical similarity"""
    if not sentiment_analyzer:
        return tracks
    
    try:
        user_sentiment = sentiment_analyzer(user_description)[0]
        original_audio_features = get_audio_features(original_track['id'], token) if token else None
        scored_tracks = []
        
        for track in tracks:
            score = ai_score_track(track, user_sentiment, user_description, original_audio_features, token)
            scored_tracks.append((track, score))
        
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        return [track for track, score in scored_tracks]
        
    except Exception as e:
        print(f"AI filtering error: {e}")
        return tracks

def ai_score_track(track, user_sentiment, user_description, original_audio_features=None, token=None):
    """Score tracks prioritizing musical similarity then user preferences"""
    score = 50
    match_quality = 'yellow'  # Default
    
    try:
        # Get audio features for similarity scoring
        if original_audio_features and token:
            track_features = get_audio_features(track['id'], token)
            if track_features:
                similarity_points = 0
                
                # Tempo similarity (most important)
                tempo_diff = abs(original_audio_features.get('tempo', 120) - track_features.get('tempo', 120))
                if tempo_diff < 10:
                    score += 50
                    similarity_points += 3
                elif tempo_diff < 25:
                    score += 30
                    similarity_points += 2
                elif tempo_diff < 40:
                    score += 15
                    similarity_points += 1
                
                # Energy similarity
                energy_diff = abs(original_audio_features.get('energy', 0.5) - track_features.get('energy', 0.5))
                if energy_diff < 0.15:
                    score += 40
                    similarity_points += 3
                elif energy_diff < 0.3:
                    score += 20
                    similarity_points += 2
                elif energy_diff < 0.5:
                    score += 10
                    similarity_points += 1
                
                # Valence similarity
                valence_diff = abs(original_audio_features.get('valence', 0.5) - track_features.get('valence', 0.5))
                if valence_diff < 0.2:
                    score += 35
                    similarity_points += 3
                elif valence_diff < 0.4:
                    score += 18
                    similarity_points += 2
                elif valence_diff < 0.6:
                    score += 8
                    similarity_points += 1
                
                # Danceability similarity
                dance_diff = abs(original_audio_features.get('danceability', 0.5) - track_features.get('danceability', 0.5))
                if dance_diff < 0.2:
                    score += 20
                    similarity_points += 1
                
                # Determine match quality based on similarity points
                if similarity_points >= 8:
                    match_quality = 'green'  # Excellent match
                elif similarity_points >= 5:
                    match_quality = 'yellow'  # Good match
                else:
                    match_quality = 'red'  # Weak match
        
        # Secondary scoring: sentiment alignment
        if sentiment_analyzer:
            track_text = f"{track['name']} {track['artists'][0]['name']}"
            track_sentiment = sentiment_analyzer(track_text)[0]
            
            if user_sentiment['label'] == track_sentiment['label']:
                score += 10
        
        # Store match quality in track for sorting
        track['match_quality'] = match_quality
        track['similarity_score'] = score
        
        return score
        
    except Exception as e:
        print(f"Scoring error: {e}")
        track['match_quality'] = 'yellow'
        track['similarity_score'] = 50
        return 50



def get_access_token():
    if not CLIENT_ID or not CLIENT_SECRET:
        return None
        
    auth_string = f"{CLIENT_ID}:{CLIENT_SECRET}"
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = base64.b64encode(auth_bytes).decode('utf-8')
    
    response = requests.post(
        'https://accounts.spotify.com/api/token',
        headers={'Authorization': f'Basic {auth_base64}'},
        data={'grant_type': 'client_credentials'}
    )
    
    if response.status_code == 200:
        return response.json().get('access_token')
    return None

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

@app.route('/api/ai-recommendations', methods=['POST'])
def get_ai_recommendations():
    
    data = request.get_json()
    track_id = data.get('trackId')
    user_description = data.get('userDescription', '')
    
    if not track_id:
        return jsonify({'error': 'Track ID required'}), 400
    
    token = get_access_token()
    if not token:
        return jsonify({'error': 'Failed to get access token'}), 500
    
    # Get track details
    track_response = requests.get(
        f'https://api.spotify.com/v1/tracks/{track_id}',
        headers={'Authorization': f'Bearer {token}'}
    )
    
    if track_response.status_code != 200:
        return jsonify({'error': 'Track not found'}), 404
    
    track_data = track_response.json()
    recommendations = []
    existing_ids = {track_id}
    artist_id = track_data['artists'][0]['id']
    artist_name = track_data['artists'][0]['name']
    
    # Step 1: Get AI recommendations
    ai_song_queries = generate_ai_recommendations_with_explanations(user_description, track_data, token)
    
    # Step 2: Search for each AI recommendation on Spotify and generate explanations
    for song_query in ai_song_queries:
        if len(recommendations) >= 9:
            break
            
        # Search for the song on Spotify
        search_response = requests.get(
            f'https://api.spotify.com/v1/search?q={song_query}&type=track&limit=3&market=US',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if search_response.status_code == 200:
            search_tracks = search_response.json()['tracks']['items']
            
            for track in search_tracks:
                if (track['id'] not in existing_ids and 
                    len(recommendations) < 9):
                    # Generate individual explanation for this specific song
                    track['ai_explanation'] = generate_individual_explanation(song_query, track_data, user_description, token)
                    recommendations.append(track)
                    existing_ids.add(track['id'])
                    break
    
    # If we don't have enough recommendations, try broader searches
    if len(recommendations) < 6:
        broader_queries = [
            f"{artist_name} similar",
            f"artists like {artist_name}",
            f"songs similar to {track_data['name']}"
        ]
        
        for query in broader_queries:
            if len(recommendations) >= 9:
                break
                
            search_response = requests.get(
                f'https://api.spotify.com/v1/search?q={query}&type=track&limit=10&market=US',
                headers={'Authorization': f'Bearer {token}'}
            )
            
            if search_response.status_code == 200:
                search_tracks = search_response.json()['tracks']['items']
                filtered_tracks = ai_filter_recommendations(search_tracks, user_description, track_data, token)
                
                for track in filtered_tracks[:3]:  # Take top 3 from each broader search
                    if (track['id'] not in existing_ids and 
                        len(recommendations) < 9):
                        # Generate explanation for fallback tracks too
                        track_query = f"{track['artists'][0]['name']} - {track['name']}"
                        track['ai_explanation'] = generate_individual_explanation(track_query, track_data, user_description, token)
                        recommendations.append(track)
                        existing_ids.add(track['id'])
    
    # Explanations already generated for each track in the search loop above
    
    # Sort by match quality: green first, then yellow, then red
    quality_order = {'green': 0, 'yellow': 1, 'red': 2}
    recommendations.sort(key=lambda x: (quality_order.get(x.get('match_quality', 'yellow'), 1), -x.get('similarity_score', 50)))
    
    return jsonify({
        'tracks': recommendations,
        'debug': f'AI recommended {len(recommendations)} songs sorted by similarity strength'
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)