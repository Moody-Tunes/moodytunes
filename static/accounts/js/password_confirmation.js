'use strict';

(function IIFE(){
    let form = document.getElementById('password-form');
    form.addEventListener('submit', validateMatchingPassword);

    function validateMatchingPassword(evt) {
        // If there are any Django validation errors, hide them
        // This is a new submission, don't display old errors
        let errorListContainer = document.getElementById('errorlist-container');
        if (errorListContainer) {
            errorListContainer.hidden = true;
        }

        // Validate that `confirm_password` and `password_fields` match
        // Expects there to be a hidden div with id `password-error` to display
        let errorMessage = document.getElementById('password-error');
        let passwordField = document.getElementById('id_password');
        let confirmPasswordField = document.getElementById('id_confirm_password');

        if (passwordField.value && passwordField.value !== confirmPasswordField.value) {
            evt.preventDefault();
            errorMessage.hidden = false;
        }

    }
})();
