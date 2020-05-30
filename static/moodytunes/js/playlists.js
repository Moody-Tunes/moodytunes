'use strict';

(function IIFE() {
    // Global variables for API requests to backend
    // Made global to ensure that the same options used in the request are
    // used in requests for voting on songs
    let emotion;
    let generatePlaylistButton = document.getElementById('generate-playlist');
    let confirmDeleteModal = document.getElementById('delete-confirm-modal');
    let closeModal = document.getElementById('close-modal');
    let cancelDeleteVoteButton = document.getElementById('cancel-delete-vote');
    let confirmDeleteVoteButton = document.getElementById('delete-vote');

    // Cache options for previous request, used for refreshing playlist on delete of vote
    let lastGenre,
        lastContext;

    function hideConfirmDeleteModal() {
        confirmDeleteModal.style.display = 'none';
    }

    function showConfirmDeleteModal() {
        confirmDeleteModal.style.display = 'block';
    }

    function deleteVote(evt) {
        let song = confirmDeleteVoteButton.dataset.song;
        hideConfirmDeleteModal();
        document.MoodyTunesClient.deleteVote(song, emotion, lastContext, data => {
            getEmotionPlaylist(evt);
        });
    }

    function init() {
        closeModal.addEventListener('click', hideConfirmDeleteModal);
        cancelDeleteVoteButton.addEventListener('click', hideConfirmDeleteModal);
        confirmDeleteVoteButton.addEventListener('click', deleteVote);
        generatePlaylistButton.addEventListener('click', getEmotionPlaylist);
    }

    function confirmDeleteVote() {
        cancelDeleteVoteButton.disabled = false;
        confirmDeleteVoteButton.disabled = false;
        confirmDeleteVoteButton.dataset.song = this.dataset.song;
        showConfirmDeleteModal();
    }

    function createDeleteButton(song) {
        let buttonContainer = document.createElement('div');
        buttonContainer.className = 'vote-button-container';

        let button = document.createElement('button');
        button.className = 'vote-button vote-button-delete';
        button.appendChild(document.createTextNode('Delete'));
        button.dataset.song = song;
        button.addEventListener('click', confirmDeleteVote);
        buttonContainer.appendChild(button);

        return buttonContainer
    }

    function createPaginationButton(link, type) {
        let name = type.charAt(0).toUpperCase() + type.slice(1);
        let button = document.createElement('button');
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
            document.getElementById('analytics-danceability').innerText = data.danceability && data.danceability.toPrecision(2);
            document.getElementById('analytics-total-songs').innerText = data.total_songs;
        }
    }

    function getPaginatedEmotionPlaylist() {
        let url = this.dataset.url;
        let options = {
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
        let playlistContainer = document.getElementById('playlist-display-container');
        let buttonContainer = document.getElementById('playlist-pagination-button-container');
        let noResultsFoundAlert = document.getElementById('alert-no-results');

        let votes = data.results;
        let nextLink = data.next;
        let previousLink = data.previous;

        document.PlaylistCurator.clearChildren(playlistContainer);
        document.PlaylistCurator.clearChildren(buttonContainer);
        document.PlaylistCurator.clearChildren(document.getElementById('playlist-error-container'));
        noResultsFoundAlert.hidden = true;  // Default to hide alert that no results are displayed

        if (data.errors) {
            document.PlaylistCurator.displayRequestErrors(data.errors);
        } else {
            if (document.PlaylistCurator.isEmptyResult(data.count)) {
                noResultsFoundAlert.hidden = false;
                return;
            }

            votes.forEach(vote => {
                let song = vote.song;

                let songContainer = document.createElement('div');
                songContainer.id = 'song-' + song.code;
                songContainer.className = 'song-container';

                songContainer.appendChild(document.PlaylistCurator.createPlayButton(song));

                let descriptionContainer = document.createElement('p');
                descriptionContainer.className = 'song-description-container';
                descriptionContainer.innerText = vote.description;
                songContainer.appendChild(descriptionContainer);
                songContainer.appendChild(createDeleteButton(song.code));

                playlistContainer.appendChild(songContainer);
            });

            // Add buttons to retrieve paginated responses
            if (nextLink || previousLink) {
                buttonContainer.appendChild(createPaginationButton(previousLink, 'previous'));
                buttonContainer.appendChild(createPaginationButton(nextLink, 'next'));
            }
        }
    }

    function getEmotionPlaylist(evt) {
        let genre,
            context;

        if (evt.target === generatePlaylistButton) {
            // Pull request parameters from form options
            emotion = document.getElementById('id_emotion').value;
            genre = document.getElementById('id_genre').value || undefined;
            context = document.getElementById('id_context').value || undefined;

            lastGenre = genre;
            lastContext = context;
        } else {
            // Used cached parameters for persistent queries (on delete vote requests)
            genre = lastGenre;
            context = lastContext;
        }

        document.MoodyTunesClient.getEmotionPlaylist(emotion, genre, context, displayEmotionPlaylist);
        document.MoodyTunesClient.getUserAnalytics(emotion, genre, context, displayAnalytics);
    }

    init();
})();
