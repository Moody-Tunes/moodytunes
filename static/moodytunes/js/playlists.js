'use strict';

(function IIFE() {
    // Global variables for API requests to backend
    // Made global to ensure that the same options used in the request are
    // used in requests for voting on songs
    let emotion;
    let generatePlaylistButton = document.getElementById('generate-playlist');

    let closeDeleteModal = document.getElementById('close-delete-modal');
    let confirmDeleteModal = document.getElementById('delete-confirm-modal');
    let cancelDeleteVoteButton = document.getElementById('cancel-delete-vote');
    let confirmDeleteVoteButton = document.getElementById('delete-vote');

    let closeSuccessDeleteModal = document.getElementById('close-delete-success-modal');
    let successDeleteModal = document.getElementById('delete-success-modal');

    let closeAddContextModal = document.getElementById('close-add-context-modal');
    let cancelAddContextModal = document.getElementById('cancel-add-context-to-vote-button');
    let confirmAddContextModal = document.getElementById('add-context-confirm-modal');

    let closeSuccessAddContextModal = document.getElementById('close-add-context-success-modal');
    let successAddContextModal = document.getElementById('add-context-success-modal');

    // Cache options for previous request, used for refreshing playlist on delete of vote
    let lastGenre,
        lastContext,
        lastArtist;

    function hideConfirmDeleteModal() {
        confirmDeleteModal.style.display = 'none';
    }

    function showConfirmDeleteModal() {
        confirmDeleteModal.style.display = 'block';
    }

    function hideSuccessDeleteModal() {
        successDeleteModal.style.display = 'none';
    }

    function showSuccessDeleteModal() {
        successDeleteModal.style.display = 'block';
    }

    function hideConfirmAddContextModal() {
        confirmAddContextModal.style.display = 'none';
    }

    function showConfirmAddContextModal() {
        confirmAddContextModal.style.display = 'block';
    }

    function hideSuccessAddContextModal() {
        successAddContextModal.style.display = 'none';
    }

    function showSuccessAddContextModal() {
        successAddContextModal.style.display = 'block';
    }

    function deleteVote(evt) {
        let song = confirmDeleteVoteButton.dataset.song;
        hideConfirmDeleteModal();
        document.MoodyTunesClient.deleteVote(song, emotion, lastContext, data => {
            let messageContainer = document.getElementById('delete-success-content');
            messageContainer.innerText = 'Successfully deleted song from your playlist!';
            showSuccessDeleteModal();
            getEmotionPlaylist(evt);
        });
    }

    function addContextToVote(evt) {
        hideConfirmAddContextModal();

        let song = this.dataset.songCode;
        let context = document.getElementById('add-context-input').value;

        document.MoodyTunesClient.postVote(song, emotion, context, '', true, data => {
            successAddContextToVote(context);
        });
    }

    function init() {
        closeDeleteModal.addEventListener('click', hideConfirmDeleteModal);
        closeAddContextModal.addEventListener('click', hideConfirmAddContextModal);
        closeSuccessAddContextModal.addEventListener('click', hideSuccessAddContextModal);
        closeSuccessDeleteModal.addEventListener('click', hideSuccessDeleteModal);

        window.onclick = function (evt) {
            if (evt.target === confirmDeleteModal) {
                hideConfirmDeleteModal();
            } else if (evt.target === confirmAddContextModal) {
                hideConfirmAddContextModal();
            } else if (evt.target === successAddContextModal) {
                hideSuccessAddContextModal();
            } else if (evt.target === successDeleteModal) {
                hideSuccessDeleteModal();
            }
        };

        cancelAddContextModal.addEventListener('click', hideConfirmAddContextModal);
        cancelDeleteVoteButton.addEventListener('click', hideConfirmDeleteModal);
        confirmDeleteVoteButton.addEventListener('click', deleteVote);
        generatePlaylistButton.addEventListener('click', getEmotionPlaylist);

        // Generate browse playlist on enter key press
        document.addEventListener('keyup', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                generatePlaylistButton.click();
            }
        });
    }

    function successAddContextToVote(context) {
        let messageContainer = document.getElementById('add-context-success-content');
        messageContainer.innerText = 'Successfully added song to your ' + context.toLowerCase() + ' playlist!';
        showSuccessAddContextModal();
    }

    function confirmDeleteVote() {
        cancelDeleteVoteButton.disabled = false;
        confirmDeleteVoteButton.disabled = false;
        confirmDeleteVoteButton.dataset.song = this.dataset.song;
        showConfirmDeleteModal();
    }

    function confirmAddContextToVote(songCode, contexts) {
        let helpMessage = document.getElementById('add-context-help-text');
        let unavailableMessage = document.getElementById('add-context-unavailable-text');

        let confirmAddContextButton = document.getElementById('add-context-to-vote-button');
        confirmAddContextButton.dataset.songCode = songCode;
        confirmAddContextButton.addEventListener('click', addContextToVote);

        let confirmAddContextInput = document.getElementById('add-context-input');
        document.PlaylistCurator.clearChildren(confirmAddContextInput);

        helpMessage.hidden = false;
        unavailableMessage.hidden = true;
        confirmAddContextButton.hidden = false;
        confirmAddContextInput.hidden = false;

        // Display message if there are no available contexts to add to song
        if (Object.keys(contexts).length === 0) {
            helpMessage.hidden = true;
            unavailableMessage.hidden = false;
            confirmAddContextButton.hidden = true;
            confirmAddContextInput.hidden = true;
        } else {
            contexts.forEach( context => {
                let newOption = document.createElement('option');
                newOption.appendChild(document.createTextNode(context.name));
                newOption.value = context.code;
                confirmAddContextInput.appendChild(newOption);
            });
        }

        showConfirmAddContextModal();
    }

    function showContextsToAddForVote() {
        let song = this.dataset.song;
        let availableContexts = [];

        document.MoodyTunesClient.getOptions(function (data) {
            data.contexts.forEach( obj => {
                if (obj.code !== "") {
                    availableContexts.push({code: obj.code, name: obj.name});
                }
            });

            document.MoodyTunesClient.getInfoForVote(song, emotion, function (data) {
                let contexts = data.contexts;
                let optionContexts = availableContexts.filter(context => !contexts.includes(context.code));

                confirmAddContextToVote(song, optionContexts);
            });
        });
    }

    function createDeleteButton(song) {
        let button = document.createElement('button');
        button.className = 'vote-button vote-button-delete';
        button.appendChild(document.createTextNode('Delete'));
        button.dataset.song = song;
        button.addEventListener('click', confirmDeleteVote);

        return button;
    }

    function createAddContextButton(song) {
        let button = document.createElement('button');
        button.className = 'vote-button vote-button-context';
        button.appendChild(document.createTextNode('Add Context'));
        button.dataset.song = song;
        button.addEventListener('click', showContextsToAddForVote);

        return button;
    }

    function createButtons(song) {
        let buttonContainer = document.createElement('div');
        buttonContainer.className = 'vote-button-container';

        buttonContainer.appendChild(createDeleteButton(song));
        buttonContainer.appendChild(createAddContextButton(song));

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
            document.getElementById('analytics-total-songs').innerText = data.count;
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
        displayAnalytics(data);
        let playlistContainer = document.getElementById('playlist-display-container');
        let buttonContainer = document.getElementById('playlist-pagination-button-container');
        let noResultsFoundAlert = document.getElementById('alert-no-results');

        let votes = data.results;
        let nextLink = data.next;
        let previousLink = data.previous;

        document.PlaylistCurator.clearChildren(playlistContainer);
        document.PlaylistCurator.clearChildren(buttonContainer);
        noResultsFoundAlert.hidden = true;  // Default to hide alert that no results are displayed

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
            let voteButtons = createButtons(song.code);
            songContainer.appendChild(voteButtons);

            let descriptionContainer = document.createElement('p');
            descriptionContainer.className = 'song-description-container';
            descriptionContainer.innerText = vote.description;
            voteButtons.appendChild(descriptionContainer);

            playlistContainer.appendChild(songContainer);
        });

        // Add buttons to retrieve paginated responses
        if (nextLink || previousLink) {
            let firstLink = data.first_page;
            let lastLink = data.last_page;

            buttonContainer.appendChild(createPaginationButton(firstLink, 'first'));
            buttonContainer.appendChild(createPaginationButton(previousLink, 'previous'));
            buttonContainer.appendChild(createPaginationButton(nextLink, 'next'));
            buttonContainer.appendChild(createPaginationButton(lastLink, 'last'));
        }
    }

    function getEmotionPlaylist(evt) {
        let genre,
            context,
            artist;

        let artistInput = document.getElementById('id_artist');

        if (evt.target === generatePlaylistButton) {
            // Pull request parameters from form options
            emotion = document.getElementById('id_emotion').value;
            genre = document.getElementById('id_genre').value || undefined;
            context = document.getElementById('id_context').value || undefined;
            artist = artistInput && artistInput.value || undefined;

            lastGenre = genre;
            lastContext = context;
            lastArtist = artist;
        } else {
            // Used cached parameters for persistent queries (on delete vote requests)
            genre = lastGenre;
            context = lastContext;
            artist = lastArtist;
        }

        document.MoodyTunesClient.getEmotionPlaylist(emotion, genre, context, artist, displayEmotionPlaylist);
    }

    init();
})();
