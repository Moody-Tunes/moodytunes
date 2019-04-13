(function IIFE() {
    function setUpContextModal() {
        var modal = document.getElementById('context-modal');
        var closeModal = document.getElementById('close-modal');
        var clearContext = document.getElementById('clear-context');
        var showModal = document.getElementById('set-context-button');
        var submitModal = document.getElementById('submit-context');

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
        var jitterInput = document.getElementById('id_jitter');
        var jitterOutput = document.getElementById('jitter-value');
        jitterOutput.innerText = jitterInput.value;

        jitterInput.oninput = function () {
            var jitterValue = Number.parseFloat(this.value);
            jitterOutput.innerText = jitterValue.toFixed(2);
        }
    }

    function voteOnSong() {
        var emotion = document.getElementById('id_emotion').value;
        var context = sessionStorage.context;
        var description = sessionStorage.description;
        var song = this.dataset.song;
        var vote = this.dataset.vote;

        document.MoodyTunesClient.postVote(song, emotion, context, description, vote, function(data) {
            // Disable buttons to prevent double votes for a track
            var songContainer = document.getElementById('song-' + song);
            var voteButtons = songContainer.querySelectorAll('button');

            for (var i=0; i<voteButtons.length; i++) {
                var button = voteButtons[i];
                button.disabled = true;

                if (button.dataset.vote === vote) {
                    button.className += ' vote-button-' + vote + '-chosen';
                }
            }
        })
    }

    function createVoteButton(voteValue, song) {
        var button = document.createElement('button');
        button.className = 'vote-button vote-button-' + voteValue;
        var name = voteValue ? 'Yes' : 'No';
        button.appendChild(document.createTextNode(name));
        button.dataset.song = song.code;
        button.dataset.vote = voteValue;
        button.addEventListener('click', voteOnSong);

        return button
    }

    function createVoteButtons(song) {
        var buttonContainer = document.createElement('div');
        buttonContainer.className = 'vote-button-container';

        buttonContainer.appendChild(createVoteButton(true, song));
        buttonContainer.appendChild(createVoteButton(false, song));

        return buttonContainer;
    }

    function createPlayButton(song) {
        var playButton = document.createElement('iframe');
        playButton.className = 'play-button';
        playButton.src = 'https://embed.spotify.com/?uri=' + song.code;

        return playButton
    }

    function createSong(song) {
        var songContainer = document.createElement('div');
        songContainer.id = 'song-' + song.code;
        songContainer.className = 'song-container';

        songContainer.appendChild(createPlayButton(song));
        songContainer.appendChild(createVoteButtons(song));

        return songContainer;
    }

    function displayBrowsePlaylist(data) {
        var playlistContainer = document.getElementById('playlist-display-container');
        var noResultsFoundAlert = document.getElementById('alert-no-results');
        noResultsFoundAlert.hidden = true;  // Default to hide alert that no results are displayed

        document.PlaylistCurator.clearChildren(playlistContainer);
        document.PlaylistCurator.clearChildren(document.getElementById('playlist-error-container'));

        if (data.errors) {
            document.PlaylistCurator.displayRequestErrors(data.errors);
        } else {
            noResultsFoundAlert.hidden = data.length >= 1;  // Show alert if we don't get any data back

            // Build playlist from returned data
            for (var i = 0; i < data.length; i++) {
                playlistContainer.appendChild(createSong(data[i]));
            }
        }
    }

    function getBrowsePlaylist() {
        var limit = undefined; // We don't want people to set the limit themselves, keep it at the default

        var context = sessionStorage.context;
        var emotion = document.getElementById('id_emotion').value;
        var jitter = document.getElementById('id_jitter').value;
        var genre = document.getElementById('id_genre').value || undefined;

        document.MoodyTunesClient.getBrowsePlaylist(
            emotion, jitter, limit, genre, context, displayBrowsePlaylist
        );
    }

    setUpContextModal();
    setUpJitterInput();
    var generatePlaylistButton = document.getElementById('generate-playlist');
    generatePlaylistButton.addEventListener('click', getBrowsePlaylist);
})();
