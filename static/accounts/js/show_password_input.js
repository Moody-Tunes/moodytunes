'use strict';

(function IIFE() {
    let showPasswordInput = document.getElementById('show-password');
    let passwordInput = document.getElementById('id_password');
    let confirmPasswordInput = document.getElementById('id_confirm_password');

    showPasswordInput.addEventListener('click', function () {
        const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        passwordInput.setAttribute('type', type);
        confirmPasswordInput.setAttribute('type', type);

        let showPasswordImage = showPasswordInput.dataset.showPasswordImg;
        if (type === 'text') {
            showPasswordImage = showPasswordInput.dataset.hidePasswordImg;
        }

        showPasswordInput.setAttribute('src', showPasswordImage);
    })
})();
