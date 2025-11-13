# Setup Instructions

## 1. Get Spotify Client Credentials
- Go to https://developer.spotify.com/dashboard
- Create an app or use existing one
- Copy Client ID and Client Secret

## 2. Install Dependencies
```bash
pip install -r requirements.txt
```

## 3. Configure Credentials
- Copy `.env.example` to `.env`
- Open `.env` file
- Replace `your_client_id_here` with your Client ID
- Replace `your_client_secret_here` with your Client Secret

## 4. Run Backend
```bash
python server.py
```

## 5. Run Frontend
- Open `index.html` in browser at `http://localhost:5000`
- Or serve static files through Flask

## 6. Usage
1. Search for a song you love
2. Click "Get Recommendations" on any result
3. Browse the recommended songs

## Architecture
- **Frontend**: HTML/JS (calls backend API)
- **Backend**: Flask server (proxies Spotify API)
- **Security**: Token hidden on server-side