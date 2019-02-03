(function IIFE() {
    function deleteVote() {
        var emotion = document.getElementById('id_emotion').value;
        var song = this.dataset.song;

        document.MoodyTunesClient.deleteVote(song, emotion, function(data) {
            var songContainer = document.getElementById('song-' + song);
            songContainer.hidden = true;
        })
    }

    function createDeleteButton(song) {
        var button = document.createElement('button');
        button.appendChild(document.createTextNode('Delete'));
        button.dataset.song = song;
        button.addEventListener('click', deleteVote);

        return button
    }

    function displayAnalytics(data) {
        document.getElementById('analytics-emotion').innerText = data.emotion_name;
        document.getElementById('analytics-energy').innerText = data.energy.toPrecision(2);
        document.getElementById('analytics-valence').innerText = data.valence.toPrecision(2);
        document.getElementById('analytics-total-songs').innerText = data.total_songs;
    }

    function displayEmotionPlaylist(data) {
        var playlistContainer = document.getElementById('playlist-display-container');
        var noResultsFoundAlert = document.getElementById('alert-no-results');
        noResultsFoundAlert.hidden = data.length > 1;  // Show alert if we don't get any data back

        // Clean out playlist if there are any old songs still present
        while(playlistContainer.hasChildNodes()) {
            playlistContainer.removeChild(playlistContainer.firstChild);
        }

        // Create list for play buttons
        var playButtonList = document.createElement('ul');

        for (var i=0; i<data.length; i++) {
            var vote = data[i];
            var song = vote.song;

            var listRecord = document.createElement('li');
            var songContainer = document.createElement('div');
            listRecord.id = 'song-' + song.code;

            // Generate Spotify play button for track and add to playlist
            var playButton = document.createElement('iframe');
            playButton.src = 'https://embed.spotify.com/?uri=' + song.code;
            songContainer.appendChild(playButton);

            // Generate delete button
            songContainer.appendChild(createDeleteButton(song.code));

            listRecord.appendChild(songContainer);
            playButtonList.appendChild(listRecord);
        }

        playlistContainer.appendChild(playButtonList);
    }

    function getEmotionPlaylist() {
        var emotion = document.getElementById('id_emotion').value;
        var genre = document.getElementById('id_genre').value || undefined;
        var context = document.getElementById('id_context').value || undefined;

        document.MoodyTunesClient.getEmotionPlaylist(emotion, genre, context, displayEmotionPlaylist);
        document.MoodyTunesClient.getUserAnalytics(emotion, genre, displayAnalytics)
    }

    var generatePlaylistButton = document.getElementById('generate-playlist');
    generatePlaylistButton.onclick = getEmotionPlaylist;
})();