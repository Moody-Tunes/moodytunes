import json
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
from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.generics import get_object_or_404

from accounts.forms import CreateUserForm, UpdateUserForm
from accounts.models import MoodyUser, UserProfile
from accounts.serializers import UserProfileRequestSerializer, UserProfileSerializer
from base.mixins import PatchRequestValidatorMixin
from base.views import FormView
from libs.moody_logging import auto_fingerprint, update_logging_data
from spotify.models import SpotifyAuth


logger = logging.getLogger(__name__)


class MoodyLoginView(LoginView):
    template_name = 'login.html'
    redirect_authenticated_user = True

    def get_redirect_url(self):
        redirect_url = super().get_redirect_url()

        if not redirect_url:
            show_spotify_auth = False

            if waffle.switch_is_active('show_spotify_auth_prompt'):

                if self.request.user.is_authenticated:
                    if not self.request.user.userprofile.has_rejected_spotify_auth:
                        show_spotify_auth = not SpotifyAuth.objects.filter(user=self.request.user).exists()

                        if not show_spotify_auth:
                            # This means the user has already authenticated with Spotify, but because their
                            # UserProfile record indicates that they have not rejected to auth with Spotify we will
                            # continue to do multiple queries to determine their authentication status.
                            # We should update their profile value here to reflect they have "rejected" to auth
                            # with Spotify by virtue of them already doing so.
                            # TODO: Should we rename this field on UserProfile then?
                            #  Maybe `has_authenticated_with_spotify`?
                            self.request.user.userprofile.has_rejected_spotify_auth = True
                            self.request.user.userprofile.save()

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

        return super().get_next_page()


class MoodyPasswordResetView(PasswordResetView):
    success_url = settings.LOGIN_URL
    template_name = 'password_reset.html'
    email_template_name = 'password_reset_email.html'

    def form_valid(self, form):
        messages.info(self.request, 'We have sent a password reset email to the address provided.')
        return super().form_valid(form)


class MoodyPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'password_change.html'
    success_url = reverse_lazy('accounts:password-reset-complete')


class MoodyPasswordResetDone(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if not self.request.user.is_authenticated:
            messages.info(self.request, 'Please login with your new password.')
            return settings.LOGIN_URL
        else:
            messages.info(self.request, 'Your password has been updated!')
            return settings.LOGIN_REDIRECT_URL


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

    @update_logging_data
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            request.user.update_information(form.cleaned_data)
            messages.info(request, 'Your account information has been updated.')

            return HttpResponseRedirect(reverse('accounts:profile'))
        else:
            logger.warning(
                'Failed to update user info because of invalid data',
                extra={
                    'errors': form.errors,
                    'request_data': {
                        'username': request.POST.get('username'),
                        'email': request.POST.get('email')
                    },
                    'user_id': request.user.id,
                    'fingerprint': auto_fingerprint('failed_to_update_user_info', **kwargs),
                    'trace_id': request.trace_id,
                }
            )
            return render(request, self.template_name, {'form': form})


class CreateUserView(FormView):
    form_class = CreateUserForm
    template_name = 'create.html'

    @update_logging_data
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = MoodyUser(
                username=form.cleaned_data['username'],
                email=form.cleaned_data.get('email'),
            )

            user.set_password(form.cleaned_data['password'])
            user._trace_id = request.trace_id
            user.save()

            UserProfile.objects.create(user=user)

            logger.info(
                'Created new user: {}'.format(user.username),
                extra={
                    'fingerprint': auto_fingerprint('created_new_user', **kwargs),
                    'trace_id': request.trace_id,
                }
            )

            messages.info(request, 'Your account has been created.')

            return HttpResponseRedirect(settings.LOGIN_URL)
        else:
            logger.warning(
                'Failed to create new user because of invalid data',
                extra={
                    'errors': form.errors,
                    'request_data': {
                        'username': request.POST.get('username'),
                        'email': request.POST.get('email')
                    },
                    'fingerprint': auto_fingerprint('failed_to_create_new_user', **kwargs),
                    'trace_id': request.trace_id
                }
            )

            return render(request, self.template_name, {'form': form})


class UserProfileView(PatchRequestValidatorMixin, generics.RetrieveAPIView, generics.UpdateAPIView):
    """
    get: Retrieve the UserProfile data for the request user

    patch: Update the UserProfile record with provided data for the request user
    """
    serializer_class = UserProfileSerializer

    patch_request_serializer = UserProfileRequestSerializer

    http_method_names = ['get', 'patch']

    if settings.DEBUG:  # pragma: no cover
        from base.documentation_utils import MultipleMethodSchema
        schema = MultipleMethodSchema(
            patch_request_serializer=UserProfileRequestSerializer,
        )

    @swagger_auto_schema(
        request_body=UserProfileRequestSerializer(),
        responses={status.HTTP_200_OK: json.dumps({'status': 'OK'})}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

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
                'trace_id': request.trace_id
            }
        )

        return JsonResponse({'status': 'OK'})
