(function IIFE() {
    let showHelpButton = document.getElementById('show-help');
    let helpContainer = document.getElementById('help-container');

    showHelpButton.addEventListener('click', function(){
        helpContainer.hidden = false;
        showHelpButton.hidden = true;
    });
})();
