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
                <div class="user-input-section">
                    <h4>Why do you like this song?</h4>
                    <textarea id="userDescription" placeholder="The beat, lyrics, mood, energy, memories..." onkeypress="handleDescriptionKeyPress(event, '${track.id}')"></textarea>
                    <button class="rec-btn" id="aiRecBtn" onclick="getAIRecommendations('${track.id}')">Get AI-Powered Recommendations</button>
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
        };
        
        div.appendChild(songInfo);
        div.appendChild(button);
        resultsDiv.appendChild(div);
    });
}

function createLoadingPulse() {
    return `
        <div class="loading-pulse">
            <div class="loading-bar" style="background: #0f5132;"></div>
            <div class="loading-bar" style="background: #0f5132;"></div>
            <div class="loading-bar" style="background: #0f5132;"></div>
        </div>
    `;
}

async function getAIRecommendations(trackId) {
    const userDescription = document.getElementById('userDescription').value;
    
    if (!userDescription.trim()) {
        alert('Please tell us why you love this song first!');
        return;
    }
    
    // Show loading state on button
    const button = document.getElementById('aiRecBtn');
    const originalText = button.innerHTML;
    button.innerHTML = `Finding matches... ${createLoadingPulse()}`;
    button.disabled = true;
    

    
    try {
        const response = await fetch('/api/ai-recommendations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                trackId: trackId,
                userDescription: userDescription
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            console.error('API Error:', data.error, data.debug);
            document.getElementById('recommendations').innerHTML = `<p>Error: ${data.error}</p>`;
            return;
        }
        
        console.log('Debug info:', data.debug);
        
        // First fade out the user input section
        const userInputSection = document.querySelector('.user-input-section');
        if (userInputSection) {
            userInputSection.style.transition = 'all 0.5s ease-out';
            userInputSection.style.opacity = '0';
            userInputSection.style.transform = 'translateY(-20px)';
            
            setTimeout(() => {
                userInputSection.remove();
                // Then display recommendations after input section is gone
                displayRecommendations(data.tracks);
            }, 500);
        } else {
            displayRecommendations(data.tracks);
        }
    } catch (error) {
        console.error('AI Recommendations failed:', error);
        document.getElementById('recommendations').innerHTML = `<p>Error: ${error.message}</p>`;
    } finally {
        // Reset button
        button.innerHTML = originalText;
        button.disabled = false;
    }
}

function handleDescriptionKeyPress(event, trackId) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        getAIRecommendations(trackId);
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
        
        // Add hover tooltip for AI explanation
        if (track.ai_explanation) {
            div.setAttribute('data-explanation', track.ai_explanation);
            div.classList.add('has-explanation');
        }
        
        div.appendChild(songInfo);
        div.appendChild(linkDiv);
        gridDiv.appendChild(div);
    });
}