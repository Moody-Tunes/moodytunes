import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordResetConfirmView
from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, resolve, Resolver404, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views import View
from django.views.generic.base import TemplateView, RedirectView
from rest_framework import generics

from accounts.forms import CreateUserForm, UpdateUserForm
from accounts.models import MoodyUser, UserSongVote
from accounts.serializers import AnalyticsSerializer, AnalyticsRequestSerializer
from accounts.utils import filter_duplicate_votes_on_song_from_playlist
from base.mixins import GetRequestValidatorMixin
from tunes.models import Emotion
from libs.utils import average

logger = logging.getLogger(__name__)


class MoodyLoginView(LoginView):
    template_name = 'login.html'

    def get_redirect_url(self):
        redirect_url = super().get_redirect_url()

        if not redirect_url:
            # If no redirect URL provided, redirect to default login redirect
            return settings.LOGIN_REDIRECT_URL

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
class UpdateInfoView(View):
    form_class = UpdateUserForm
    template_name = 'update.html'

    def get(self, request):
        # Construct password reset link for user
        # Logic for constructing uid64 and token are lifted from Django's password reset form
        password_reset_link = reverse(
            'accounts:password-reset-confirm',
            kwargs={
                'uidb64': urlsafe_base64_encode(force_bytes(self.request.user.pk)).decode(),
                'token': default_token_generator.make_token(self.request.user)
            }
        )

        initial_data = {
            'username': self.request.user.username,
            'email': self.request.user.email
        }

        form = self.form_class(initial=initial_data, user=request.user)
        context = {
            'form': form,
            'password_reset_link': password_reset_link
        }

        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, user=request.user)

        if form.is_valid():
            request.user.update_information(form.cleaned_data)
            messages.info(request, 'Your account information has been updated.')

            return HttpResponseRedirect(reverse('accounts:profile'))
        else:
            return render(request, self.template_name, {'form': form})


class CreateUserView(View):
    form_class = CreateUserForm
    template_name = 'create.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = MoodyUser.objects.create(username=form.cleaned_data['username'])
            user.email = form.cleaned_data.get('email')
            user.set_password(form.cleaned_data['password'])
            user.save()

            logger.info('Created new user: {}'.format(user.username))
            messages.info(request, 'Your account has been created.')

            return HttpResponseRedirect(reverse('accounts:login'))
        else:
            return render(request, self.template_name, {'form': form})


class AnalyticsView(GetRequestValidatorMixin, generics.RetrieveAPIView):
    serializer_class = AnalyticsSerializer

    get_request_serializer = AnalyticsRequestSerializer

    def get_object(self):
        energy = None
        valence = None
        context = self.cleaned_data.get('context')
        genre = self.cleaned_data.get('genre')

        emotion = Emotion.objects.get(name=self.cleaned_data['emotion'])
        votes_for_emotion = UserSongVote.objects.filter(
            user=self.request.user,
            emotion=emotion,
            vote=True
        )

        if votes_for_emotion.exists():
            if context:
                votes_for_emotion = votes_for_emotion.filter(context=context)

            if genre:
                votes_for_emotion = votes_for_emotion.filter(song__genre=genre)

            votes_for_emotion = filter_duplicate_votes_on_song_from_playlist(votes_for_emotion)

            energy = average(votes_for_emotion.values_list('song__energy', flat=True))
            valence = average(votes_for_emotion.values_list('song__valence', flat=True))

        data = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': genre,
            'energy': energy,
            'valence': valence,
            'total_songs': votes_for_emotion.count()
        }

        return data
