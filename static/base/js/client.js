'use strict';

(function IIFE() {
    document.MoodyTunesClient = {
        /*
        Client for interacting with the MoodyTunes backend API. Exposes a set of functions that are meant to retrieve
        data necessary for user interaction with the site, like retrieving playlists of songs to browse, retrieving a
        playlists of songs that a user has voted as making them feel a certain emotion, voting on songs, and deleting
        previous votes for a song.

        Each function expects to receive the data necessary for making a request to the API as arguments. In the case
        of optional arguments (like genre for retrieving songs) the argument passed  should be `undefined`. In addition,
        the last argument to each function should be a callback function that processes the data retrieved from the
        API. This function (on successful requests) receives the JSON data from the API as argument and can work with
        the data in the context of the page (like appending Spotify play buttons to a section or writing the data to an
        element on the page).
        */
        checkTruthyObject: function(obj) {
            // Return whether or not `obj` is a Javascript Object and is empty
            return Boolean(obj && obj.constructor === Object && Object.entries(obj).length !== 0);
        },
        buildRequestURL: function(endpoint, params) {
            // Build a URL for making a request to the backend API
            // @endpoint (str): Path in the API to make a request (ex /tunes/browse)
            // @params (object): Query parameters to append to request url
            // :return (str): Full url for API request
            var requestUrl = new URL(window.location.origin + endpoint);

            if (this.checkTruthyObject(params)) {
                for (var key in params) {
                    if (params.hasOwnProperty(key)) {
                        requestUrl.searchParams.append(key, params[key]);
                    }
                }
            }

            return requestUrl;
        },
        stripNullParams: function(params) {
            // Strips null values from params to ensure that URL doesn't include undefined parameters
            // @params (object): Query params to include in request
            // :return (object): Same params passed in, minus any keys that have undefined values
            if (this.checkTruthyObject(params)) {
                for (var key in params) {
                    if (params.hasOwnProperty(key) && params[key] === undefined) {
                        delete params[key];
                    }
                }
            }

            return params;
        },
        getCookie: function(name) {
            // Retrieve a cookie value by name from the session cookie
            // Lifted from Django documentation https://docs.djangoproject.com/en/2.1/ref/csrf/
            // @param name (str): Name of cookie to retrieve
            // :return (str, undefined): Cookie value if present in session cookie or undefined if not found
            var cookieValue = null;

            if (document.cookie && document.cookie !== '') {
                var cookies = document.cookie.split(';');
                for (var i=0; i < cookies.length; i++) {
                    var cookie = cookies[i].trim();
                    if (cookie.substring(0, name.length + 1) === (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }

            return cookieValue;
        },
        request: function(method, endpoint, params, data, callback) {
            // Wrapper for making request to MoodyTunes API
            // @method (str): Request method to use in request (GET, POST, DELETE)
            // @endpoint (str): Path in the API to make a request (ex /tunes/browse)
            // @params (object): Query parameters to include in request
            // @data (object): Request data to send (used for POST and DELETE methods)
            // @callback (function): Callback function to pass retrieved data onto
            //      -> This is what will consume the data retrieved from the request
            var url = this.buildRequestURL(endpoint, this.stripNullParams(params));
            var options = {
                method: method,
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (method !== 'GET') {
                options.body = JSON.stringify(data);
                options.headers['X-CSRFToken'] = this.getCookie('csrftoken');
            }

            fetch(url, options)
                .then((response) => {
                    return response.json();
                }).then((json) => {
                    callback(json);
                });
        },
        getOptions: function(callback) {
            // Retrieve options for site interaction (emotions and genres in our system)
            // Used to build options for users to choose from when generating playlists to listen to
            this.request('GET', '/tunes/options/', {}, {}, callback);
        },
        getUserAnalytics: function(emotion, genre, context, callback) {
            // Retrieve analytics for users based on what songs they've listened to
            var params = {
                emotion: emotion,
                genre: genre,
                context: context,
            };
            this.request('GET', '/accounts/analytics/', params, {}, callback);
        },
        getBrowsePlaylist: function(emotion, jitter, limit, genre, context, returnLast, callback) {
            // Retrieve a playlist of songs for a user to listen to and decide whether or not they make them feel
            // their desired emotion
            var params = {
                emotion: emotion,
                jitter: jitter,
                limit: limit,
                genre: genre,
                context: context,
                return_last: returnLast,
            };

            this.request('GET', '/tunes/browse/', params, {}, callback);
        },
        getCachedBrowsePlaylsit: function(callback) {
            // Retrieve the last viewed browse playlist for the user
            var paramas = {
                return_last: true
            };

            this.request('GET', '/tunes/browse', paramas, {}, callback);
        },
        getEmotionPlaylist: function(emotion, genre, context, callback) {
            // Retrieve a playlist of songs the user has previously voted as making them feel a desired emotion
            var params = {
                emotion: emotion,
                genre: genre,
                context: context
            };

            this.request('GET', '/tunes/playlist/', params, {}, callback);
        },
        postVote: function(songCode, emotion, context, description, vote, callback) {
            // Register a vote for a song in our system based on whether or not the song makes the user feel
            // the desired emotion
            var data = {
                song_code: songCode,
                emotion: emotion,
                context: context,
                description: description,
                vote: vote
            };
            this.request('POST', '/tunes/vote/', {}, data, callback);
        },
        deleteVote: function(songCode, emotion, context, callback) {
            // "Unvote" a song the user has previously reported as making them feel the desired emotion
            var data = {
                song_code: songCode,
                emotion: emotion,
                context: context,
            };
            this.request('DELETE', '/tunes/vote/', {}, data, callback);
        }
    };
})();
