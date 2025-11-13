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
        model="gpt2",
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

def generate_recommendation_explanation(recommended_track, user_description, original_track, token=None):
    """Generate unique, detailed explanations for each recommendation"""
    rec_artist = recommended_track['artists'][0]['name']
    orig_artist = original_track['artists'][0]['name']
    rec_title = recommended_track['name']
    orig_title = original_track['name']
    
    # Get audio features for detailed comparison
    orig_features = get_audio_features(original_track['id'], token) if token else None
    rec_features = get_audio_features(recommended_track['id'], token) if token else None
    
    if orig_features and rec_features:
        # Create unique seed based on track ID for consistent randomization
        track_seed = hash(recommended_track['id']) % 1000
        random.seed(track_seed)
        
        # Analyze specific musical similarities with varied descriptions
        similarities = []
        
        # Tempo analysis with variations
        orig_tempo = int(orig_features.get('tempo', 120))
        rec_tempo = int(rec_features.get('tempo', 120))
        tempo_diff = abs(orig_tempo - rec_tempo)
        
        if tempo_diff < 10:
            tempo_phrases = [f"locks into the exact {orig_tempo} BPM groove", f"matches the precise {orig_tempo} BPM pulse", f"shares the identical {orig_tempo} BPM heartbeat"]
            similarities.append(random.choice(tempo_phrases))
        elif tempo_diff < 25:
            tempo_phrases = [f"rides a similar {rec_tempo} BPM wave to the {orig_tempo} BPM original", f"pulses at {rec_tempo} BPM, echoing the {orig_tempo} BPM drive"]
            similarities.append(random.choice(tempo_phrases))
        
        # Energy analysis with unique descriptors
        orig_energy = orig_features.get('energy', 0.5)
        rec_energy = rec_features.get('energy', 0.5)
        energy_diff = abs(orig_energy - rec_energy)
        
        if energy_diff < 0.15:
            if orig_energy > 0.7:
                energy_phrases = ["blazing intensity", "electric dynamism", "raw kinetic power", "explosive sonic force"]
            elif orig_energy < 0.3:
                energy_phrases = ["gentle restraint", "whispered intimacy", "delicate subtlety", "hushed vulnerability"]
            else:
                energy_phrases = ["measured intensity", "controlled dynamics", "balanced momentum", "steady emotional pull"]
            similarities.append(random.choice(energy_phrases))
        
        # Valence with emotional variety
        orig_valence = orig_features.get('valence', 0.5)
        rec_valence = rec_features.get('valence', 0.5)
        valence_diff = abs(orig_valence - rec_valence)
        
        if valence_diff < 0.2:
            if orig_valence > 0.7:
                mood_phrases = ["radiant optimism", "soaring euphoria", "infectious joy", "luminous positivity"]
            elif orig_valence < 0.3:
                mood_phrases = ["wistful melancholy", "introspective darkness", "haunting sadness", "contemplative sorrow"]
            else:
                mood_phrases = ["nuanced emotional depth", "complex tonal balance", "layered emotional texture", "sophisticated mood palette"]
            similarities.append(random.choice(mood_phrases))
        
        # Unique contextual elements
        contexts = []
        
        # Year context with variety
        orig_year = original_track.get('album', {}).get('release_date', '')[:4]
        rec_year = recommended_track.get('album', {}).get('release_date', '')[:4]
        
        if orig_year and rec_year and orig_year.isdigit() and rec_year.isdigit():
            year_diff = int(rec_year) - int(orig_year)
            if abs(year_diff) > 10:
                year_phrases = [f"Spanning {abs(year_diff)} years from {rec_year}", f"A {rec_year} gem that bridges decades", f"From {rec_year}, proving timeless appeal"]
                contexts.append(random.choice(year_phrases))
        
        # Artist connection variety
        if rec_artist.lower() != orig_artist.lower():
            artist_phrases = [f"{rec_artist} channels similar creative energy", f"{rec_artist} explores parallel sonic territory", f"{rec_artist} taps into the same musical vein"]
            contexts.append(random.choice(artist_phrases))
        
        # Build completely unique explanation
        if similarities:
            # Vary sentence structure
            structures = [
                f"'{rec_title}' delivers {similarities[0]} that defines '{orig_title}'.",
                f"Like '{orig_title}', '{rec_title}' captures {similarities[0]}.",
                f"'{rec_title}' mirrors the {similarities[0]} of '{orig_title}'.",
                f"The {similarities[0]} in '{rec_title}' echoes '{orig_title}' perfectly."
            ]
            
            explanation = random.choice(structures)
            
            if contexts:
                explanation += f" {random.choice(contexts)}."
            
            return explanation
    
    # Unique fallback variations
    fallbacks = [
        f"'{rec_title}' resonates with the same musical DNA as '{orig_title}'.",
        f"'{rec_title}' captures the essence that makes '{orig_title}' special.",
        f"'{rec_title}' shares the core appeal of '{orig_title}'."
    ]
    return random.choice(fallbacks)

def generate_sentiment_explanation(recommended_track, user_description, original_track):
    """Generate explanation using sentiment analysis"""
    if not sentiment_analyzer:
        return f"'{recommended_track['name']}' by {recommended_track['artists'][0]['name']} matches your musical taste."
    
    try:
        # Analyze sentiment of user description
        user_sentiment = sentiment_analyzer(user_description)[0]
        
        # Analyze sentiment of track titles
        track_sentiment = sentiment_analyzer(f"{recommended_track['name']} {recommended_track['artists'][0]['name']}")[0]
        
        rec_title = recommended_track['name']
        rec_artist = recommended_track['artists'][0]['name']
        orig_title = original_track['name']
        
        # Generate explanation based on sentiment matching
        if user_sentiment['label'] == 'POSITIVE' and track_sentiment['label'] == 'POSITIVE':
            return f"'{rec_title}' by {rec_artist} captures the same uplifting energy and positive emotions you connected with in '{orig_title}'."
        elif user_sentiment['label'] == 'NEGATIVE' and track_sentiment['label'] == 'NEGATIVE':
            return f"'{rec_title}' by {rec_artist} explores similar emotional depth and vulnerability that resonated with you."
        elif user_sentiment['label'] == 'POSITIVE' and track_sentiment['label'] == 'NEGATIVE':
            return f"'{rec_title}' by {rec_artist} offers an emotional contrast that complements your appreciation for diverse musical experiences."
        else:
            return f"'{rec_title}' by {rec_artist} shares the balanced emotional complexity you appreciated in your description."
            
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return f"'{recommended_track['name']}' by {recommended_track['artists'][0]['name']} aligns with your musical preferences."

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
    import time
    time.sleep(2)  # Add loading delay
    
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
    
    # Let AI determine what songs to recommend based on user description and audio features
    ai_recommendations = generate_ai_song_recommendations(user_description, track_data, token)
    
    # Search for the AI-recommended songs on Spotify with multiple strategies
    for song_query in ai_recommendations:
        if len(recommendations) >= 9:
            break
            
        # Try exact search first
        search_response = requests.get(
            f'https://api.spotify.com/v1/search?q={song_query}&type=track&limit=5&market=US',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        if search_response.status_code == 200:
            search_tracks = search_response.json()['tracks']['items']
            
            # Filter and score tracks using AI
            filtered_tracks = ai_filter_recommendations(search_tracks, user_description, track_data, token)
            
            for track in filtered_tracks:
                if (track['id'] not in existing_ids and 
                    len(recommendations) < 9):
                    recommendations.append(track)
                    existing_ids.add(track['id'])
                    break  # Only take best match per AI recommendation
    
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
                        recommendations.append(track)
                        existing_ids.add(track['id'])
    
    # Add AI explanations to each track (AI already chose these specifically)
    for track in recommendations:
        track['ai_explanation'] = generate_recommendation_explanation(track, user_description, track_data, token)
    
    # Sort by match quality: green first, then yellow, then red
    quality_order = {'green': 0, 'yellow': 1, 'red': 2}
    recommendations.sort(key=lambda x: (quality_order.get(x.get('match_quality', 'yellow'), 1), -x.get('similarity_score', 50)))
    
    return jsonify({
        'tracks': recommendations,
        'debug': f'AI recommended {len(recommendations)} songs sorted by similarity strength'
    })

if __name__ == '__main__':
    app.run(debug=True, port=8000)