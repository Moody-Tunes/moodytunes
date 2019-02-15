'use strict';

(function IIFE() {
    function deleteVote() {
        var emotion = document.getElementById('id_emotion').value;
        var song = this.dataset.song;

        document.MoodyTunesClient.deleteVote(song, emotion, function(data) {
            // Disable buttons to prevent double votes for a track
            var songContainer = document.getElementById('song-' + song);
            songContainer.className += ' song-container-vote-delete';
            var button = songContainer.querySelectorAll('button')[0];  // We've only got the one delete button
            button.disabled = true;
            button.className += ' vote-button-delete-chosen';
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
            songContainer.appendChild(createDeleteButton(song.code));

            playlistContainer.appendChild(songContainer);
        }

        // Add buttons to retrieve paginated responses
        if (nextLink || previousLink) {
            var previousButton = document.createElement('button');
            previousButton.appendChild(document.createTextNode('Previous'));
            previousButton.className = 'previous-button';
            previousButton.dataset.url = previousLink;
            previousButton.addEventListener('click', getPaginatedEmotionPlaylist);
            previousButton.disabled = !previousLink;  // Disable button if there is no next URL

            var nextButton = document.createElement('button');
            nextButton.appendChild(document.createTextNode('Next'));
            nextButton.className = 'next-button';
            nextButton.dataset.url = nextLink;
            nextButton.addEventListener('click', getPaginatedEmotionPlaylist);
            nextButton.disabled = !nextLink;  // Disable button if there is no next URL

            buttonContainer.appendChild(previousButton);
            buttonContainer.appendChild(nextButton);
        }
    }

    function getEmotionPlaylist() {
        var emotion = document.getElementById('id_emotion').value;
        var genre = document.getElementById('id_genre').value || undefined;
        var context = document.getElementById('id_context').value || undefined;

        document.MoodyTunesClient.getEmotionPlaylist(emotion, genre, context, displayEmotionPlaylist);
        document.MoodyTunesClient.getUserAnalytics(emotion, genre, displayAnalytics)
    }

    var generatePlaylistButton = document.getElementById('generate-playlist');
    generatePlaylistButton.onclick = getEmotionPlaylist;
})();