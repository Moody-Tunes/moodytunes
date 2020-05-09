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
        createPlayButton: function(song) {
            let playButton = document.createElement('iframe');
            playButton.setAttribute('allow', 'encrypted-media https://open.spotify.com;');
            playButton.className = 'play-button';
            playButton.src = 'https://embed.spotify.com/?uri=' + song.code;

            return playButton
        },
        isEmptyResult: function(results) {
            return !Boolean(results);
        }
    }
})();
