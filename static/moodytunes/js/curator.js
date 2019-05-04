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
            var errorContainer = document.getElementById('playlist-error-container');

            // Clean out older errors
            while (errorContainer.hasChildNodes()) {
                this.clearChildren(errorContainer);
            }

            var errorList = document.createElement('ul');

            for (var key in errors) {
                if (errors.hasOwnProperty(key)) {
                    var error = document.createElement('li');
                    error.innerText = key + ': ' + errors[key];
                    errorList.appendChild(error);
                }
            }

            errorContainer.appendChild(errorList);
        },
        createPlayButton: function(song) {
            var playButton = document.createElement('iframe');
            playButton.className = 'play-button';
            playButton.src = 'https://embed.spotify.com/?uri=' + song.code;

            return playButton
        }
    }
})();
