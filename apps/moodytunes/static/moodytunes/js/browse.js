(function IIFE() {
    function displayBrowsePlayList(data) {
        var playlistContainer = document.getElementById('playlist-display-container');

        // Clean out playlist if there are any old songs still present
        while(playlistContainer.hasChildNodes()) {
            playlistContainer.removeChild(playlistContainer.firstChild);
        }

        // Create list for play buttons
        var playButtonList = document.createElement('ul');

        for (var i=0; i<data.length; i++) {
            var song = data[i];
            var listRecord = document.createElement('li');

            // Generate Spotify play button for track and add to playlist
            var playButton = document.createElement('iframe');
            playButton.src = 'https://embed.spotify.com/?uri=' + song.code;

            listRecord.appendChild(playButton);
            playButtonList.appendChild(listRecord);
        }

        playlistContainer.appendChild(playButtonList);
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
