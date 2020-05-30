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
        displayRequestErrors: function(errors) {
            // Display validation in an error container
            let errorContainer = document.getElementById('playlist-error-container');

            // Clean out older errors
            while (errorContainer.hasChildNodes()) {
                this.clearChildren(errorContainer);
            }

            let errorList = document.createElement('ul');

            for (let key in errors) {
                if (errors.hasOwnProperty(key)) {
                    let error = document.createElement('li');
                    error.innerText = key + ': ' + errors[key];
                    errorList.appendChild(error);
                }
            }

            errorContainer.appendChild(errorList);
        },
        displayAPIErrors: function(error) {
            // Display API error message in modal
            let container = document.getElementById('container');

            // Delete old error modal if present
            let oldErrorModal = document.getElementById('error-modal');

            if (oldErrorModal) {
                container.removeChild(oldErrorModal);
            }

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
