(function IIFE() {
    function voteOnSong() {
        var emotion = document.getElementById('id_emotion').value;
        var song = this.dataset.song;
        var vote = this.dataset.vote;

        document.MoodyTunesClient.postVote(song, emotion, vote, function(data) {
            // Hide container holding song to prevent double votes
            var songContainer = document.getElementById('song-' + song);
            songContainer.hidden = true;
        })
    }

    function createVoteButton(voteValue, song) {
        var name = voteValue ? 'Upvote' : 'Downvote';
        var button = document.createElement('button');
        button.appendChild(document.createTextNode(name));
        button.dataset.song = song;
        button.dataset.vote = voteValue;
        button.addEventListener('click', voteOnSong);

        return button
    }

    function displayBrowsePlayList(data) {
        var playlistContainer = document.getElementById('playlist-display-container');

        // Clean out playlist if there are any old songs still present
        while(playlistContainer.hasChildNodes()) {
            playlistContainer.removeChild(playlistContainer.firstChild);
        }

        // Check if we didn't got any songs back
        if (data.length === 0) {
            var message = document.createElement('p');
            message.innerText = 'We were unable to find any songs for you to browse!';
            playlistContainer.appendChild(message);

            return;
        }

        // Create list for play buttons
        var playButtonList = document.createElement('ul');

        for (var i=0; i<data.length; i++) {
            var song = data[i];
            var listRecord = document.createElement('li');
            var songContainer = document.createElement('div');
            listRecord.id = 'song-' + song.code;

            // Generate Spotify play button for track and add to playlist
            var playButton = document.createElement('iframe');
            playButton.src = 'https://embed.spotify.com/?uri=' + song.code;
            songContainer.appendChild(playButton);

            // Generate voting buttons
            songContainer.appendChild(createVoteButton(true, song.code));
            songContainer.appendChild(createVoteButton(false, song.code));

            listRecord.appendChild(songContainer);
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
