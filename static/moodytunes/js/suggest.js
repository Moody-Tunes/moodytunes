(function IIFE() {
    var showHelpButton = document.getElementById('show-help');
    var helpContainer = document.getElementById('help-container');

    showHelpButton.addEventListener('click', function(){
        helpContainer.hidden = false;
        showHelpButton.hidden = true;
    });
})();
