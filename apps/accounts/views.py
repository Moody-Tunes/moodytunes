import logging

import waffle
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView,
    LogoutView,
    PasswordChangeView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import Resolver404, resolve, reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic.base import RedirectView, TemplateView
from rest_framework import generics
from rest_framework.generics import get_object_or_404

from accounts.forms import CreateUserForm, UpdateUserForm
from accounts.models import MoodyUser, SpotifyUserAuth, UserProfile
from accounts.serializers import UserProfileRequestSerializer, UserProfileSerializer
from base.mixins import PatchRequestValidatorMixin
from base.views import FormView
from libs.moody_logging import auto_fingerprint, update_logging_data


logger = logging.getLogger(__name__)


class MoodyLoginView(LoginView):
    template_name = 'login.html'

    def get_redirect_url(self):
        redirect_url = super().get_redirect_url()

        if not redirect_url:
            show_spotify_auth = False

            if waffle.switch_is_active('show_spotify_auth_prompt'):

                # Check if user has authenticated with Spotify, to prompt user to
                # authenticate if they have not already done so
                if self.request.user.is_authenticated:
                    show_spotify_auth = not SpotifyUserAuth.objects.filter(user=self.request.user).exists()

                    # Check if user has explicitly indicated they do not want to
                    # authenticate with Spotify
                    if show_spotify_auth and hasattr(self.request.user, 'userprofile'):
                        user_profile = self.request.user.userprofile
                        show_spotify_auth = not user_profile.has_rejected_spotify_auth

            return f'{settings.LOGIN_REDIRECT_URL}?show_spotify_auth={show_spotify_auth}'

        try:
            # Try to resolve the URL, if it is a valid path in our system it will return
            # without errors and we can proceed with the redirect
            resolve(redirect_url)
            return redirect_url
        except Resolver404:
            # The supplied path is not one we have in our system, report the invalid
            # redirect and raise an exception indicating suspicious operation
            logger.error('Suspicious redirect detected for {}'.format(redirect_url))
            raise SuspiciousOperation


@method_decorator(login_required, name='dispatch')
class MoodyLogoutView(LogoutView):
    def get_next_page(self):
        if self.request.host.name == 'www':
            self.next_page = settings.LOGIN_URL
        elif self.request.host.name == 'admin':
            self.next_page = '/'

        return super(MoodyLogoutView, self).get_next_page()


class MoodyPasswordResetView(PasswordResetView):
    success_url = settings.LOGIN_URL
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'

    def form_valid(self, form):
        messages.info(self.request, 'We have sent a password reset email to the address provided')
        return super().form_valid(form)


class MoodyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('accounts:password-reset-complete')


class MoodyPasswordResetDone(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        messages.info(self.request, 'Please login with your new password')
        return settings.LOGIN_URL


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'profile.html'


@method_decorator(login_required, name='dispatch')
class MoodyPasswordChangeView(PasswordChangeView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('accounts:password-reset-complete')


@method_decorator(login_required, name='dispatch')
class UpdateInfoView(FormView):
    form_class = UpdateUserForm
    template_name = 'update.html'

    def get_form_instance(self):
        initial_data = {
            'username': self.request.user.username,
            'email': self.request.user.email
        }

        return self.form_class(initial=initial_data, user=self.request.user)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            request.user.update_information(form.cleaned_data)
            messages.info(request, 'Your account information has been updated.')

            return HttpResponseRedirect(reverse('accounts:profile'))
        else:
            return render(request, self.template_name, {'form': form})


class CreateUserView(FormView):
    form_class = CreateUserForm
    template_name = 'create.html'

    @update_logging_data
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = MoodyUser.objects.create(username=form.cleaned_data['username'])
            user.email = form.cleaned_data.get('email')
            user.set_password(form.cleaned_data['password'])
            user.save()

            UserProfile.objects.create(user=user)

            logger.info(
                'Created new user: {}'.format(user.username),
                extra={'fingerprint': auto_fingerprint('created_new_user', **kwargs)}
            )

            UserProfile.objects.create(user=user)

            messages.info(request, 'Your account has been created.')

            return HttpResponseRedirect(reverse('accounts:login'))
        else:
            return render(request, self.template_name, {'form': form})


class UserProfileView(PatchRequestValidatorMixin, generics.RetrieveAPIView, generics.UpdateAPIView):
    serializer_class = UserProfileSerializer

    patch_request_serializer = UserProfileRequestSerializer

    def get_object(self):
        user_profile = get_object_or_404(UserProfile, user=self.request.user)
        return user_profile

    @update_logging_data
    def update(self, request, *args, **kwargs):
        user_profile = get_object_or_404(UserProfile, user=request.user)

        for name, value in self.cleaned_data.items():
            setattr(user_profile, name, value)

        user_profile.save()

        logger.info(
            'Updated UserProfile record for user {}'.format(request.user.username),
            extra={
                'fingerprint': auto_fingerprint('updated_user_profile', **kwargs),
                'request_data': self.cleaned_data,
            }
        )

        return JsonResponse({'status': 'OK'})
