'use strict';

(function IIFE() {
    let HttpStatusErrorMap = {
        '400': 'Invalid request parameters',
        '403': 'Request forbidden',
        '404': 'Resource not found',
        '500': 'Server returned an error',
        '502': 'Could not connect to API'
    };

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
        checkTruthyObject: function (obj) {
            // Return whether or not `obj` is a Javascript Object and is empty
            return Boolean(obj && obj.constructor === Object && Object.entries(obj).length !== 0);
        },
        buildRequestURL: function (endpoint, params) {
            // Build a URL for making a request to the backend API
            // @endpoint (str): Path in the API to make a request (ex /tunes/browse)
            // @params (object): Query parameters to append to request url
            // :return (str): Full url for API request
            let requestUrl = new URL(window.location.origin + endpoint);

            if (this.checkTruthyObject(params)) {
                for (let key in params) {
                    if (params.hasOwnProperty(key)) {
                        requestUrl.searchParams.append(key, params[key]);
                    }
                }
            }

            return requestUrl;
        },
        stripNullParams: function (params) {
            // Strips null values from params to ensure that URL doesn't include undefined parameters
            // @params (object): Query params to include in request
            // :return (object): Same params passed in, minus any keys that have undefined values
            if (this.checkTruthyObject(params)) {
                for (let key in params) {
                    if (params.hasOwnProperty(key) && params[key] === undefined) {
                        delete params[key];
                    }
                }
            }

            return params;
        },
        getCSRFToken: function () {
            // Retrieve the CSRF cookie value to use in making unsafe requests

            // Simple path: fetch the CSRF token from the page config
            // Include a div with id="config" that includes the CSRF token as a dataset attribute
            let csrfToken = document.getElementById('config').dataset.csrfToken;

            if (csrfToken !== undefined && csrfToken !== null ) {
                return csrfToken;
            }

            // TODO: How else can we find the CSRF token for the request?
        },
        request: function(method, endpoint, params, data, callback) {
            // Wrapper for making request to MoodyTunes API
            // @method (str): Request method to use in request (GET, POST, DELETE)
            // @endpoint (str): Path in the API to make a request (ex /tunes/browse)
            // @params (object): Query parameters to include in request
            // @data (object): Request data to send (used for POST and DELETE methods)
            // @callback (function): Callback function to pass retrieved data onto
            //      -> This is what will consume the data retrieved from the request
            document.PlaylistCurator.clearErrorModal();
            let url = this.buildRequestURL(endpoint, this.stripNullParams(params));
            let options = {
                method: method,
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (method !== 'GET') {
                options.body = JSON.stringify(data);
                options.headers['X-CSRFToken'] = this.getCSRFToken();
            }

            fetch(url, options)
                .then((response) => {
                    if (!response.ok) {
                        if (Object.keys(HttpStatusErrorMap).includes(String(response.status))) {
                            throw HttpStatusErrorMap[response.status];
                        }

                        // Default error message
                        throw 'Error!';
                    }

                    return response.json();
                }).then((json) => {
                    callback(json);
                }).catch(error => {
                    document.PlaylistCurator.displayAPIErrors(error);
            });
        },
        getOptions: function(callback) {
            // Retrieve options for site interaction (emotions and genres in our system)
            // Used to build options for users to choose from when generating playlists to listen to
            this.request('GET', '/tunes/options/', {}, {}, callback);
        },
        getUserAnalytics: function(emotion, genre, context, artist, callback) {
            // Retrieve analytics for users based on what songs they've listened to
            let params = {
                emotion: emotion,
                genre: genre,
                context: context,
                artist: artist
            };
            this.request('GET', '/accounts/analytics/', params, {}, callback);
        },
        getBrowsePlaylist: function(emotion, jitter, limit, genre, context, description, artist, callback) {
            // Retrieve a playlist of songs for a user to listen to and decide whether or not they make them feel
            // their desired emotion
            let params = {
                emotion: emotion,
                jitter: jitter,
                limit: limit,
                genre: genre,
                context: context,
                description: description,
                artist: artist
            };

            this.request('GET', '/tunes/browse/', params, {}, callback);
        },
        getCachedBrowsePlaylist: function(callback) {
            // Retrieve the last viewed browse playlist for the user
            this.request('GET', '/tunes/browse/last/', {}, {}, callback);
        },
        getEmotionPlaylist: function(emotion, genre, context, artist, callback) {
            // Retrieve a playlist of songs the user has previously voted as making them feel a desired emotion
            let params = {
                emotion: emotion,
                genre: genre,
                context: context,
                artist: artist,
            };

            this.request('GET', '/tunes/playlist/', params, {}, callback);
        },
        postVote: function(songCode, emotion, context, description, vote, callback) {
            // Register a vote for a song in our system based on whether or not the song makes the user feel
            // the desired emotion
            let data = {
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
            let data = {
                song_code: songCode,
                emotion: emotion,
                context: context,
            };
            this.request('DELETE', '/tunes/vote/', {}, data, callback);
        }
    };
})();
