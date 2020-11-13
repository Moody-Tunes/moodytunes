'use strict';

(function IIFE(){
    function hideModal() {
        modal.style.display = 'none';
    }

    function showModal() {
        modal.style.display = 'block';
    }

    function redirectToSpotifyAuthPage() {
        window.location.href = window.location.origin + '/moodytunes/spotify/authorize/?redirect_url=' + window.location.origin
    }

    function declineSpotifyUserAuth() {
        let data = {
            has_rejected_spotify_auth: true
        };

        document.MoodyTunesClient.updateUserProfile(data, () => {
            hideModal();
        });
    }

    let modal = document.getElementById('spotify-auth-modal');
    let closeAddSpotifyAuthModal = document.getElementById('close-spotify-auth-modal');
    let cancelAddSpotifyAuth = document.getElementById('decline-spotify-auth');
    let confirmAddSpotifyAuth = document.getElementById('accept-spotify-auth');
    let config = document.getElementById('config');

    closeAddSpotifyAuthModal.addEventListener('click', hideModal);
    cancelAddSpotifyAuth.addEventListener('click', declineSpotifyUserAuth);
    confirmAddSpotifyAuth.addEventListener('click', redirectToSpotifyAuthPage);

    if (config.dataset.showSpotifyAuthPrompt === 'True') {
        showModal();
    }
})();
