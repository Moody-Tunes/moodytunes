'use strict';

(function IIFE() {
    document.MoodyTunesClient = {
        buildRequestURL: function(url, params) {
            var requestUrl = new URL(window.location.origin + url);
            for (var key in params) {
                if (params.hasOwnProperty(key)) {
                    requestUrl.searchParams.append(key, params[key]);
                }
            }

            return requestUrl;
        },
        options: function () {
            var url = this.buildRequestURL('/tunes/options/', {});

            fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
            }).then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Bad response from ' + url);
                }
            }).then((json) => {
                console.log(json);
            });
        },
        browsePlaylist: function (emotion, jitter, limit, genre) {
            var params = {
                emotion: emotion,
                jitter: jitter,
                limit: limit,
                genre: genre
            };
            for (var key in params) {
                if (params[key] === undefined) {
                    delete params[key];
                }
            }
            var url = this.buildRequestURL('/tunes/browse/', params);

            fetch(url, {
                method: 'GET',
                credentials: 'include',
                headers: {
                    'Content-Type': 'application/json'
                },
            }).then((response) => {
                if (response.ok) {
                    return response.json();
                } else {
                    throw new Error('Bad response from ' + url);
                }
            }).then((json) => {
                console.log(json);
            });
        }
    };
})();
