async function searchSongs() {
    const query = document.getElementById('songSearch').value;
    if (!query) return;
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
        const data = await response.json();
        displaySearchResults(data.tracks.items);
    } catch (error) {
        console.error('Search failed:', error);
    }
}

function displaySearchResults(tracks) {
    const resultsDiv = document.getElementById('searchResults');
    resultsDiv.innerHTML = '<h3>Select a song:</h3>';
    
    tracks.forEach(track => {
        const div = document.createElement('div');
        div.className = 'song-item';
        div.innerHTML = `
            <strong>${track.name}</strong> by ${track.artists[0].name}
            <button onclick="getRecommendations('${track.id}')">Get Recommendations</button>
        `;
        resultsDiv.appendChild(div);
    });
}

async function getRecommendations(trackId) {
    try {
        const response = await fetch(`/api/recommendations?seed_tracks=${trackId}`);
        const data = await response.json();
        displayRecommendations(data.tracks);
    } catch (error) {
        console.error('Recommendations failed:', error);
    }
}

function displayRecommendations(tracks) {
    const recDiv = document.getElementById('recommendations');
    recDiv.innerHTML = '<h3>Recommended Songs:</h3>';
    
    tracks.forEach(track => {
        const div = document.createElement('div');
        div.className = 'song-item';
        div.innerHTML = `
            <strong>${track.name}</strong> by ${track.artists[0].name}
            ${track.external_urls.spotify ? `<a href="${track.external_urls.spotify}" target="_blank">Listen</a>` : ''}
        `;
        recDiv.appendChild(div);
    });
}