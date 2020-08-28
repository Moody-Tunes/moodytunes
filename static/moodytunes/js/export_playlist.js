'use strict';

(function IIFE() {
    let form = document.getElementById('export-playlist-form');
    form.addEventListener('submit', validateFileUpload);

    function validateFileUpload(evt) {
        let maxFileSize = 256;
        let fileInput = document.getElementById('id_cover_image');
        let errorMessage = document.getElementById('error-message');
        errorMessage.hidden = true;

        if (fileInput.files.length > 0) {
            let file = fileInput.files[0];
            let fileSize = Math.round((file.size / 1024));  // In kilobytes

            // Spotify has a max size of 256 kB for image upload
            if (fileSize > maxFileSize) {
                evt.preventDefault();
                errorMessage.hidden = false;
            }
        }
    }
})();
