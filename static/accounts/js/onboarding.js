'use strict';

(function IIFE() {
    let onboardingModal = document.getElementById('onboarding-start-modal');
    let closeOnboardingModalIcon = document.getElementById('close-onboarding-modal');
    let rejectOnboardingButton = document.getElementById('reject-onboarding-button');
    let acceptOnboardingButton = document.getElementById('accept-onboarding-button');

    function hideOnboardingModal() {
        onboardingModal.style.display = 'none';
    }

    function rejectOnboarding() {
        let data = {
            has_completed_onboarding: true
        };

        document.MoodyTunesClient.updateUserProfile(data, () => {
            hideOnboardingModal();
        });
    }

    function progressOnboarding() {
        window.location.href = new URL(window.location.origin + '/moodytunes/browse/?onboarding=true');
    }

    closeOnboardingModalIcon.addEventListener('click', hideOnboardingModal);
    rejectOnboardingButton.addEventListener('click', rejectOnboarding);
    acceptOnboardingButton.addEventListener('click', progressOnboarding);
})();
