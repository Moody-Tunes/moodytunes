'use strict';

(function IIFE() {
    function deleteVote() {
        var emotion = document.getElementById('id_emotion').value;
        var song = this.dataset.song;
        var context = document.getElementById('id_context').value || undefined;

        document.MoodyTunesClient.deleteVote(song, emotion, context, function(data) {
            // Disable buttons to prevent double votes for a track
            var songContainer = document.getElementById('song-' + song);
            songContainer.className += ' song-container-vote-delete';
            var button = songContainer.querySelectorAll('button')[0];  // We've only got the one delete button
            button.disabled = true;
            button.className += ' vote-button-delete-chosen';

            // Update analytics after delete has been processed
            var genre = document.getElementById('id_genre').value || undefined;
            document.MoodyTunesClient.getUserAnalytics(emotion, genre, context, displayAnalytics);
        })
    }

    function createDeleteButton(song) {
        var buttonContainer = document.createElement('div');
        buttonContainer.className = 'vote-button-container';

        var button = document.createElement('button');
        button.className = 'vote-button vote-button-delete';
        button.appendChild(document.createTextNode('Delete'));
        button.dataset.song = song;
        button.addEventListener('click', deleteVote);
        buttonContainer.appendChild(button);

        return buttonContainer
    }

    function createPlayButton(song) {
        var playButton = document.createElement('iframe');
        playButton.className = 'play-button';
        playButton.src = 'https://embed.spotify.com/?uri=' + song.code;

        return playButton
    }

    function createPaginationButton(link, type) {
        var name = type.charAt(0).toUpperCase() + type.slice(1);
        var button = document.createElement('button');
        button.appendChild(document.createTextNode(name));
        button.className = type + '-button';
        button.dataset.url = link;
        button.addEventListener('click', getPaginatedEmotionPlaylist);
        button.disabled = !link;  // Disable button if there is no URL to request

        return button
    }

    function displayAnalytics(data) {
        document.getElementById('analytics-emotion').innerText = data.emotion_name;
        document.getElementById('analytics-energy').innerText = data.energy && data.energy.toPrecision(2);
        document.getElementById('analytics-valence').innerText = data.valence && data.valence.toPrecision(2);
        document.getElementById('analytics-total-songs').innerText = data.total_songs;
    }

    function getPaginatedEmotionPlaylist() {
        var url = this.dataset.url;
        var options = {
            method: 'GET',
            credentials: 'include',
            headers: {
                'Content-Type': 'application/json'
            }
        };

        fetch(url, options)
            .then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Bad response from ' + url);
                }
            }).then((json) => {
                displayEmotionPlaylist(json);
            });
    }

    function displayEmotionPlaylist(data) {
        var playlistContainer = document.getElementById('playlist-display-container');
        var buttonContainer = document.getElementById('playlist-pagination-button-container');
        var noResultsFoundAlert = document.getElementById('alert-no-results');

        var songs = data.results;
        var nextLink = data.next;
        var previousLink = data.previous;
        noResultsFoundAlert.hidden = data.count >= 1;  // Show alert if we don't get any data back

        // Clean out playlist if there are any old songs still present
        while(playlistContainer.hasChildNodes()) {
            playlistContainer.removeChild(playlistContainer.firstChild);
        }

        // Remove previous buttons if they exists
        while(buttonContainer.hasChildNodes()) {
            buttonContainer.removeChild(buttonContainer.firstChild);
        }

        for (var i=0; i<songs.length; i++) {
            var vote = songs[i];
            var song = vote.song;

            var songContainer = document.createElement('div');
            songContainer.id = 'song-' + song.code;
            songContainer.className = 'song-container';

            songContainer.appendChild(createPlayButton(song));

            var descriptionContainer = document.createElement('p');
            descriptionContainer.className = 'song-description-container';
            descriptionContainer.innerText = vote.description;
            songContainer.appendChild(descriptionContainer);

            songContainer.appendChild(createDeleteButton(song.code));

            playlistContainer.appendChild(songContainer);
        }

        // Add buttons to retrieve paginated responses
        if (nextLink || previousLink) {
            buttonContainer.appendChild(createPaginationButton(previousLink, 'previous'));
            buttonContainer.appendChild(createPaginationButton(nextLink, 'next'));
        }
    }

    function getEmotionPlaylist() {
        var emotion = document.getElementById('id_emotion').value;
        var genre = document.getElementById('id_genre').value || undefined;
        var context = document.getElementById('id_context').value || undefined;

        document.MoodyTunesClient.getEmotionPlaylist(emotion, genre, context, displayEmotionPlaylist);
        document.MoodyTunesClient.getUserAnalytics(emotion, genre, context, displayAnalytics);
    }

    var generatePlaylistButton = document.getElementById('generate-playlist');
    generatePlaylistButton.onclick = getEmotionPlaylist;
})();