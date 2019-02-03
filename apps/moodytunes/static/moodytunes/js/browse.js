(function IIFE() {
    function displayBrowsePlayList(data) {
        alert('Made request OK!');
        console.log('Data for playlist: ' + data);
    }

    function getBrowsePlaylist() {
        // TODO: Set these values from user input
        var jitter = undefined;
        var limit = undefined;

        var emotion = document.getElementById('id_emotion').value;
        var genre = document.getElementById('id_genre').value || undefined;
        var context = document.getElementById('id_context').value || undefined;
        var description = document.getElementById('id_description').value || undefined;

        document.MoodyTunesClient.getBrowsePlaylist(
            emotion, jitter, limit, genre, context, description, displayBrowsePlayList
        );
    }

    var generatePlaylistButton = document.getElementById('generate-playlist');
    generatePlaylistButton.onclick = getBrowsePlaylist;
})();
