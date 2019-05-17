'use strict';

(function IIFE() {
    // Global variables for API requests to backend
    // Made global to ensure that the same options used in the request are
    // used in requests for voting on songs
    var emotion;
    var generatePlaylistButton = document.getElementById('generate-playlist');

    // Cache options for previous request, used for refreshing playlist on delete of vote
    var lastGenre,
        lastContext;

    function init() {
        generatePlaylistButton.addEventListener('click', getEmotionPlaylist);
    }

    function deleteVote(evt) {
        var confirmVal = confirm('Are you sure you want to remove this song from your playlist?');

        if (confirmVal) {
            var song = this.dataset.song;

            document.MoodyTunesClient.deleteVote(song, lastEmotion, lastContext, function(data) {
                // Refresh playlist to reflect removal of song from playlist
                getEmotionPlaylist(evt);
            })
        }
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
        if (!data.errors){
            document.getElementById('analytics-emotion').innerText = data.emotion_name;
            document.getElementById('analytics-energy').innerText = data.energy && data.energy.toPrecision(2);
            document.getElementById('analytics-valence').innerText = data.valence && data.valence.toPrecision(2);
            document.getElementById('analytics-total-songs').innerText = data.total_songs;
        }
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
                return response.json();
            }).then((json) => {
                displayEmotionPlaylist(json);
            });
    }

    function displayEmotionPlaylist(data) {
        var playlistContainer = document.getElementById('playlist-display-container');
        var buttonContainer = document.getElementById('playlist-pagination-button-container');
        var noResultsFoundAlert = document.getElementById('alert-no-results');

        var votes = data.results;
        var nextLink = data.next;
        var previousLink = data.previous;

        document.PlaylistCurator.clearChildren(playlistContainer);
        document.PlaylistCurator.clearChildren(buttonContainer);
        document.PlaylistCurator.clearChildren(document.getElementById('playlist-error-container'));
        noResultsFoundAlert.hidden = true;  // Default to hide alert that no results are displayed

        if (data.errors) {
            document.PlaylistCurator.displayRequestErrors(data.errors);
        } else {
            noResultsFoundAlert.hidden = data.count >= 1;  // Show alert if we don't get any data back

            for (var i=0; i<votes.length; i++) {
                var vote = votes[i];
                var song = vote.song;

                var songContainer = document.createElement('div');
                songContainer.id = 'song-' + song.code;
                songContainer.className = 'song-container';

                songContainer.appendChild(document.PlaylistCurator.createPlayButton(song));

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
    }

    function getEmotionPlaylist(evt) {
        var genre,
            context;

        if (evt.target === generatePlaylistButton) {
            // Pull request parameters from form options
            emotion = document.getElementById('id_emotion').value;
            genre = document.getElementById('id_genre').value || undefined;
            context = document.getElementById('id_context').value || undefined;

            lastGenre = genre;
            lastContext = context;
        } else{
            // Used cached parameters for persistent queries (on delete vote requests)
            genre = lastGenre;
            context = lastContext;
        }

        document.MoodyTunesClient.getEmotionPlaylist(emotion, genre, context, displayEmotionPlaylist);
        document.MoodyTunesClient.getUserAnalytics(emotion, genre, context, displayAnalytics);
    }

    init();
})();