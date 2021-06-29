'use strict';

(function IIFE() {
    let checkbox = document.getElementById('show-password');
    let passwordInput = document.getElementById('id_password');
    let confirmPasswordInput = document.getElementById('id_confirm_password');

    checkbox.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        confirmPasswordInput.setAttribute('type', type);
    })
})();
