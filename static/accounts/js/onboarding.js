'use strict';

(function IIFE() {
    let onboardingModal = document.getElementById('onboarding-start-modal');
    let closeOnboardingModalIcon = document.getElementById('close-onboarding-modal');
    let rejectOnboardingButton = document.getElementById('reject-onboarding-button');
    let acceptOnboardingButton = document.getElementById('accept-onboarding-button');

    function hideOnboardingModal() {
        onboardingModal.style.display = 'none';
        // TODO: Set user `has_completed_onboarding` to True
    }

    function progressOnboarding() {
        window.location.href = new URL(window.location.origin + '/moodytunes/browse/?onboarding=true');
    }

    closeOnboardingModalIcon.addEventListener('click', hideOnboardingModal);
    rejectOnboardingButton.addEventListener('click', hideOnboardingModal);
    acceptOnboardingButton.addEventListener('click', progressOnboarding);
})();
