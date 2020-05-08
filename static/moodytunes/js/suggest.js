(function IIFE() {
    let showHelpButton = document.getElementById('show-help');
    let helpContainer = document.getElementById('help-container');

    showHelpButton.addEventListener('click', () => {
        helpContainer.hidden = false;
        showHelpButton.hidden = true;
    });
})();
