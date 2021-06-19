'use strict';

(function IIFE() {
    // Global variables for API requests to backend
    // Made global to ensure that the same options used in the request are
    // used in requests for voting on songs
    let emotion,
        jitter,
        genre,
        artist;

    function init() {
        setUpContextModal();
        setUpJitterInput();
        let generatePlaylistButton = document.getElementById('generate-playlist');
        let returnLastPlaylist = document.getElementById('use-cached-playlist');
        generatePlaylistButton.addEventListener('click', getBrowsePlaylist);
        returnLastPlaylist.addEventListener('click', generateLastBrowsePlaylist);

        // Generate browse playlist on enter key press
        document.addEventListener('keyup', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                generatePlaylistButton.click();
            }
        });
    }

    function setUpContextModal() {
        let modal = document.getElementById('context-modal');
        let closeModal = document.getElementById('close-modal');
        let clearContext = document.getElementById('clear-context');
        let showModal = document.getElementById('set-context-button');
        let submitModal = document.getElementById('submit-context');

        // Clear session storage to clear any previously set values
        sessionStorage.clear();

        showModal.onclick = function () {
            modal.style.display = 'block';
        };

        submitModal.onclick = function () {
            sessionStorage.context = document.getElementById('id_context').value;
            sessionStorage.description = document.getElementById('id_description').value;
            modal.style.display = 'none';
        };

        clearContext.onclick = function () {
            sessionStorage.clear();
            modal.style.display = 'none';
        };

        closeModal.onclick = function () {
            modal.style.display = 'none';
        };

        window.onclick = function (evt) {
            if (evt.target === modal) {
                modal.style.display = 'none';
            }
        };
    }

    function setUpJitterInput() {
        let jitterInput = document.getElementById('id_jitter');
        let jitterValue = document.getElementById('jitter-value');
        let maxJitter = Number.parseFloat(jitterInput.max);

        // Display the jitter value in the form as a percentage of the max jitter
        // ex: if the jitter value is 0.1, display 20% in the input ((0.1 / 0.5) * 100 = 20)
        let jitterDisplay = (Number.parseFloat(jitterInput.value) / maxJitter) * 100;
        jitterValue.innerText = jitterDisplay + '%';

        jitterInput.addEventListener('input', () => {
            // Update display of jitter value when user adjusts the input slider
            jitterDisplay = (Number.parseFloat(jitterInput.value) / maxJitter) * 100;
            jitterValue.innerText = jitterDisplay + '%';
        });
    }

    function generateLastBrowsePlaylist() {
        document.MoodyTunesClient.getCachedBrowsePlaylist(function (data) {
            emotion = data.emotion;
            sessionStorage.context = data.context || '';
            sessionStorage.description = data.description || '';
            let playlist = {results: data.playlist};
            displayBrowsePlaylist(playlist);
        });
    }

    function allSongsVotedOn() {
        // Check if all the songs from the browse playlist have been voted on
        let allSongsVotedOn = true;
        const songContainers = document.getElementsByClassName('song-container');

        for (const songContainer of songContainers) {
            if (!songContainer.dataset.votedOn) {
                allSongsVotedOn = false;
            }
        }

        return allSongsVotedOn;
    }

    function voteOnSong() {
        let context = sessionStorage.context;
        let description = sessionStorage.description;
        let song = this.dataset.song;
        let vote = this.dataset.vote;
        let traceId = sessionStorage.traceId;

        document.MoodyTunesClient.postVote(song, emotion, context, description, vote, traceId, function(data) {
            // Disable buttons to prevent double votes for a track
            let songContainer = document.getElementById('song-' + song);
            let voteButtons = songContainer.querySelectorAll('button');

            for (const voteButton of voteButtons) {
                voteButton.disabled = true;

                if (voteButton.dataset.vote === vote) {
                    voteButton.className += ' vote-button-' + vote + '-chosen';
                }
            }

            songContainer.dataset.votedOn = 'true';
            if (allSongsVotedOn()) {
                getBrowsePlaylist();
            }
        })
    }

    function createVoteButton(voteValue, song) {
        let button = document.createElement('button');
        button.className = 'vote-button vote-button-' + voteValue;
        let name = voteValue ? 'Yes' : 'No';
        button.appendChild(document.createTextNode(name));
        button.dataset.song = song.code;
        button.dataset.vote = voteValue;
        button.addEventListener('click', voteOnSong);

        return button
    }

    function createVoteButtons(song) {
        let buttonContainer = document.createElement('div');
        buttonContainer.className = 'vote-button-container';

        buttonContainer.appendChild(createVoteButton(true, song));
        buttonContainer.appendChild(createVoteButton(false, song));

        return buttonContainer;
    }

    function createSongContainer(song) {
        let songContainer = document.createElement('div');
        songContainer.id = 'song-' + song.code;
        songContainer.className = 'song-container';

        songContainer.appendChild(document.PlaylistCurator.createPlayButton(song));
        songContainer.appendChild(createVoteButtons(song));

        return songContainer;
    }

    function displayBrowsePlaylist(data) {
        let songs = data.results;
        sessionStorage.traceId = data.trace_id;
        let playlistContainer = document.getElementById('playlist-display-container');
        let noResultsFoundAlert = document.getElementById('alert-no-results');
        noResultsFoundAlert.hidden = true;  // Default to hide alert that no results are displayed

        document.PlaylistCurator.clearChildren(playlistContainer);

        if (document.PlaylistCurator.isEmptyResult(songs.length)) {
            noResultsFoundAlert.hidden = false;
            return;
        }

        // Build playlist from returned data
        for (const song of songs) {
            playlistContainer.appendChild(createSongContainer(song));
        }
    }

    function getBrowsePlaylist(evt) {
        let generatePlaylistButton = document.getElementById('generate-playlist');
        let artistInput = document.getElementById('id_artist');

        let limit; // We don't want people to set the limit themselves, keep it at the default

        let context = sessionStorage.context;
        let description = sessionStorage.description;

        // Only gather values from input on button press for generating browse playlist
        // This will ensure we persist values across refresh requests when the
        // user votes on all the songs for their browse playlist
        if (evt && evt.target === generatePlaylistButton) {
            emotion = document.getElementById('id_emotion').value;
            jitter = document.getElementById('id_jitter').value;
            genre = document.getElementById('id_genre').value || undefined;
            artist = artistInput && artistInput.value || undefined;
        }

        document.MoodyTunesClient.getBrowsePlaylist(
            emotion, jitter, limit, genre, context, description, artist, displayBrowsePlaylist
        );
    }

    init();
})();
