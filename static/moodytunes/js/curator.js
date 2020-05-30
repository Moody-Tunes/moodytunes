'use strict';

(function IIFE () {
    document.PlaylistCurator = {
        /*
        Provides functionality for building playlists of songs for browse and playlist pages.
        */
        clearChildren: function(container) {
            // Remove all children from an HTML element containing other elements
            while (container.hasChildNodes()) {
                container.removeChild(container.firstChild);
            }
        },
        clearErrorModal: function() {
            let container = document.getElementById('container');
            let oldErrorModal = document.getElementById('error-modal');

            if (oldErrorModal) {
                container.removeChild(oldErrorModal);
            }
        },
        displayAPIErrors: function(error) {
            // Delete old error modal if present
            this.clearErrorModal();

            // Display API error message in modal
            let container = document.getElementById('container');

            // Create parent modal
            let errorModal = document.createElement('div');
            errorModal.style.display =  'block';
            errorModal.id = 'error-modal';
            errorModal.className = 'modal';

            // Add ability to close modal on click outside of modal
            window.onclick = function (evt) {
                if (evt.target === errorModal) {
                    errorModal.style.display = 'none';
                }
            };

            // Add close button to modal
            let closeErrorModal = document.createElement('span');
            closeErrorModal.innerHTML = '&times;';
            closeErrorModal.className = 'close';
            closeErrorModal.onclick = function () {
                errorModal.style.display = 'none';
            };

            // Create div for modal content
            let errorModalContent = document.createElement('div');
            errorModalContent.className = 'modal-content';

            // Create div for displaying error message
            let errorContent = document.createElement('p');
            errorContent.innerText = error;

            // Build up error modal
            errorModalContent.appendChild(closeErrorModal);
            errorModalContent.appendChild(errorContent);
            errorModal.appendChild(errorModalContent);

            // Display error modal
            container.appendChild(errorModal);
        },
        createPlayButton: function(song) {
            let playButton = document.createElement('iframe');
            playButton.setAttribute('allow', 'encrypted-media https://open.spotify.com;');
            playButton.className = 'play-button';
            playButton.src = 'https://open.spotify.com/embed/track/' + song.code.split(':')[2];

            return playButton
        },
        isEmptyResult: function(results) {
            return !Boolean(results);
        }
    }
})();
