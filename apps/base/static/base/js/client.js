'use strict';

(function IIFE() {
    document.MoodyTunesClient = {
        buildRequestURL: function(endpoint, params) {
            var requestUrl = new URL(window.location.origin + endpoint);
            for (var key in params) {
                if (params.hasOwnProperty(key)) {
                    requestUrl.searchParams.append(key, params[key]);
                }
            }

            return requestUrl;
        },
        stripNullParams: function(params) {
            for (var key in params) {
                if (params.hasOwnProperty(key) && params[key] === undefined) {
                    delete params[key];
                }
            }

            return params;
        },
        getCookie: function (name) {
            // Lifted from Django documentation https://docs.djangoproject.com/en/2.1/ref/csrf/

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
        request: function (endpoint, method, params, data, callback) {
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
                    if (response.ok) {
                        return response.json();
                    } else {
                        throw new Error('Bad response from ' + url);
                    }
                }).then((json) => {
                    callback(json);
                });
        },
        getOptions: function (callback) {
            this.request('/tunes/options/', 'GET', {}, {}, callback);
        },
        getUserAnalytics: function (emotion, genre, callback) {
            var params = {
                emotion: emotion,
                genre: genre
            };
            this.request('/accounts/analytics/', 'GET', params, {}, callback);
        },
        getBrowsePlaylist: function (emotion, jitter, limit, genre, callback) {
            var params = {
                emotion: emotion,
                jitter: jitter,
                limit: limit,
                genre: genre
            };

            this.request('/tunes/browse/', 'GET', params, {}, callback);
        },
        postVote: function(songCode, emotion, vote, callback) {
            var data = {
                song_code: songCode,
                emotion: emotion,
                vote: vote
            };
            this.request('/tunes/vote/', 'POST', {}, data, callback);
        }
    };
})();
