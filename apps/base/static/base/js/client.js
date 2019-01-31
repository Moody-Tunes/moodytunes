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
        request: function (endpoint, method, params, data, callback) {
            var url = this.buildRequestURL(endpoint, this.stripNullParams(params));
            var options = {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                }
            };

            if (method !== 'GET') {
                options[body] = JSON.stringify(data);
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
        options: function (callback) {
            this.request('/tunes/options/', 'GET', {}, {}, callback);
        },
        browsePlaylist: function (emotion, jitter, limit, genre, callback) {
            var params = {
                emotion: emotion,
                jitter: jitter,
                limit: limit,
                genre: genre
            };

            this.request('/tunes/browse/', 'GET', params, {}, callback);
        }
    };
})();
