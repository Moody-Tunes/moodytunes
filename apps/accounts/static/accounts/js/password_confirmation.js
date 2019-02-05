'use strict';

(function IIFE(){
    var form = document.getElementById('password-form');
    form.addEventListener('submit', validateMatchingPassword);

    function validateMatchingPassword(evt) {
        // If there are any Django validation errors, hide them
        // This is a new submission, don't display old errors
        var errorListContainer = document.getElementById('errorlist-container');
        if (errorListContainer) {
            errorListContainer.hidden = true;
        }

        // Validate that `confirm_password` and `password_fields` match
        // Expects there to be a hidden div with id `password-error` to display
        var errorMessage = document.getElementById('password-error');
        var passwordField = document.getElementById('id_password');
        var confirmPasswordField = document.getElementById('id_confirm_password');

        if (passwordField.value && passwordField.value !== confirmPasswordField.value) {
            evt.preventDefault();
            errorMessage.hidden = false;
        }

    }
})();
