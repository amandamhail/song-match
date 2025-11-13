function handleKeyPress(event) {
    if (event.key === 'Enter') {
        searchSongs();
    }
}

let currentTracks = [];

function showSelectedSong(track) {
    const resultsDiv = document.getElementById('searchResults');
    const selectedDiv = document.getElementById('selectedSong');
    
    resultsDiv.classList.add('fade-out');
    
    setTimeout(() => {
        resultsDiv.style.display = 'none';
        resultsDiv.classList.remove('fade-out');
        
        const albumCover = track.album?.images?.[0]?.url || 'https://via.placeholder.com/300x300/1db954/ffffff?text=♪';
        
        selectedDiv.innerHTML = `
            <div class="selected-song">
                <img src="${albumCover}" alt="${track.album?.name || 'Album'}" class="album-cover">
                <div class="selected-info">
                    <div class="selected-label">Selected</div>
                    <div class="song-title">${track.name}</div>
                    <div class="song-artist">${track.artists[0].name}</div>
                </div>
            </div>
        `;
    }, 500);
}

function getPopularityClass(popularity) {
    if (popularity >= 70) return 'high-popularity';
    if (popularity >= 40) return 'medium-popularity';
    return 'low-popularity';
}

async function searchSongs() {
    const query = document.getElementById('songSearch').value;
    if (!query) return;
    
    // Add pulse effect to search button
    const searchBtn = document.getElementById('searchButton');
    searchBtn.classList.add('search-pulse');
    setTimeout(() => {
        searchBtn.classList.remove('search-pulse');
    }, 600);
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        displaySearchResults(data.tracks.items);
    } catch (error) {
        console.error('Search failed:', error);
    }
}

function displaySearchResults(tracks) {
    currentTracks = tracks;
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.style.display = 'block';
    resultsDiv.innerHTML = '<h3>Select a song:</h3>';
    
    // Debug: Log track data to see what we're getting
    console.log('Track data:', tracks[0]);
    
    // Clear selected song and recommendations
    document.getElementById('selectedSong').innerHTML = '';
    document.getElementById('recommendations').innerHTML = '';
    
    tracks.forEach((track, index) => {
        const div = document.createElement('div');
        const popularityClass = getPopularityClass(track.popularity || 50);
        div.className = `song-item ${popularityClass} slide-in`;
        div.style.animationDelay = `${index * 0.1}s`;
        
        const songInfo = document.createElement('div');
        songInfo.className = 'song-info';
        songInfo.innerHTML = `
            <div class="song-title">${track.name}</div>
            <div class="song-artist">${track.artists[0].name}</div>
        `;
        
        const button = document.createElement('button');
        button.className = 'rec-btn';
        button.textContent = 'Get Recommendations';
        button.onclick = () => {
            showSelectedSong(track);
            setTimeout(() => {
                getRecommendations(track.id);
            }, 800); // Delay recommendations until after transition
        };
        
        div.appendChild(songInfo);
        div.appendChild(button);
        resultsDiv.appendChild(div);
    });
}

async function getRecommendations(trackId) {
    try {
        const response = await fetch(`/api/recommendations?seed_tracks=${trackId}`);
        const data = await response.json();
        
        if (data.error) {
            console.error('API Error:', data.error, data.details);
            document.getElementById('recommendations').innerHTML = `<p>Error: ${data.error}</p>`;
            return;
        }
        
        displayRecommendations(data.tracks);
    } catch (error) {
        console.error('Recommendations failed:', error);
        document.getElementById('recommendations').innerHTML = `<p>Error: ${error.message}</p>`;
    }
}

function displayRecommendations(tracks) {
    const recDiv = document.getElementById('recommendations');
    recDiv.innerHTML = '<h3>Recommended Songs:</h3><div class="recommendations-grid"></div>';
    const gridDiv = recDiv.querySelector('.recommendations-grid');
    
    tracks.forEach((track, index) => {
        const div = document.createElement('div');
        const popularityClass = getPopularityClass(track.popularity || 50);
        div.className = `song-item ${popularityClass} slide-in`;
        div.style.animationDelay = `${index * 0.1}s`;
        
        const songInfo = document.createElement('div');
        songInfo.className = 'song-info';
        songInfo.innerHTML = `
            <div class="song-title">${track.name}</div>
            <div class="song-artist">${track.artists[0].name}</div>
        `;
        
        const linkDiv = document.createElement('div');
        if (track.external_urls.spotify) {
            linkDiv.innerHTML = `<a href="${track.external_urls.spotify}" target="_blank" class="spotify-link">Listen on Spotify</a>`;
        }
        
        div.appendChild(songInfo);
        div.appendChild(linkDiv);
        gridDiv.appendChild(div);
    });
}