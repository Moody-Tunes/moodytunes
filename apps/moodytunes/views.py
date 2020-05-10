import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import RedirectView, TemplateView
from ratelimit.mixins import RatelimitMixin

from accounts.models import SpotifyUserAuth
from base.views import FormView
from libs.moody_logging import auto_fingerprint, update_logging_data
from libs.spotify import SpotifyClient
from moodytunes.forms import BrowseForm, ExportPlaylistForm, PlaylistForm, SuggestSongForm
from moodytunes.tasks import CreateSpotifyPlaylistFromSongsTask, FetchSongFromSpotifyTask
from moodytunes.utils import ExportPlaylistHelper
from tunes.models import Emotion
from tunes.utils import CachedPlaylistManager


logger = logging.getLogger(__name__)


class AboutView(TemplateView):
    template_name = 'about.html'


@method_decorator(login_required, name='dispatch')
class BrowsePlaylistsView(FormView):
    template_name = 'browse.html'
    form_class = BrowseForm

    def get_context_data(self, **kwargs):
        context = super(BrowsePlaylistsView, self).get_context_data(**kwargs)

        # Check if user has a cached browse playlist to retrieve
        cached_playlist_manager = CachedPlaylistManager()
        cached_playlist = cached_playlist_manager.retrieve_cached_browse_playlist(self.request.user)
        context['cached_playlist_exists'] = cached_playlist is not None

        return context


@method_decorator(login_required, name='dispatch')
class EmotionPlaylistsView(FormView):
    template_name = 'playlists.html'
    form_class = PlaylistForm

    def get_form_instance(self):
        return self.form_class(user=self.request.user)


@method_decorator(login_required, name='dispatch')
class SuggestSongView(RatelimitMixin, FormView):
    template_name = 'suggest.html'
    form_class = SuggestSongForm

    ratelimit_key = 'user'
    ratelimit_rate = '3/m'
    ratelimit_method = 'POST'

    @update_logging_data
    def post(self, request, *args, **kwargs):
        # Check if request is rate limited,
        if getattr(request, 'limited', False):
            logger.warning(
                'User {} has been rate limited from suggesting songs'.format(request.user.username),
                extra={
                    'fingerprint': auto_fingerprint('rate_limit_suggest_song', **kwargs),
                    'user_id': request.user.id
                }
            )
            messages.error(request, 'You have submitted too many suggestions! Try again in a minute')
            return HttpResponseRedirect(reverse('moodytunes:suggest'))

        form = self.form_class(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']
            FetchSongFromSpotifyTask().delay(code, username=request.user.username)

            logger.info(
                'Called task to add suggestion for song {} by user {}'.format(code, request.user.username),
                extra={'fingerprint': auto_fingerprint('added_suggested_song', **kwargs)}
            )
            messages.info(request, 'Your song has been slated to be added! Keep an eye out for it in the future')

            return HttpResponseRedirect(reverse('moodytunes:suggest'))
        else:
            logger.warning(
                'User {} suggested an invalid song code: {}. Reason: {}'.format(
                    request.user.username,
                    request.POST.get('code'),
                    form.errors['code'][0]
                ),
                extra={'fingerprint': auto_fingerprint('invalid_suggested_song', **kwargs)}
            )
            return render(request, self.template_name, context={'form': form})


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationView(TemplateView):
    template_name = 'spotify_auth.html'

    def get_context_data(self, **kwargs):
        context = super(SpotifyAuthenticationView, self).get_context_data(**kwargs)
        state = get_random_string(length=48)

        context['spotify_auth_url'] = SpotifyClient.build_spotify_oauth_confirm_link(state)

        self.request.session['state'] = state

        return context


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationCallbackView(View):

    @update_logging_data
    def get(self, request, *args, **kwargs):
        # Check to make sure that the user who initiated the request is the one making the request
        # state value for session is set in initial authentication request
        if request.GET.get('state') != request.session['state']:
            logger.error(
                'User {} has an invalid state parameter for OAuth callback'.format(request.user.username),
                extra={
                    'session_state': request.session.get('state'),
                    'request_state': request.GET.get('state'),
                    'fingerprint': auto_fingerprint('invalid_oauth_state', **kwargs)
                }
            )

            raise SuspiciousOperation('Invalid state parameter')

        if 'code' in request.GET:
            code = request.GET['code']
            user = request.user

            # Early exit: if we already have a SpotifyAuth record for the user, exit
            if SpotifyUserAuth.objects.filter(user=user).exists():
                messages.info(request, 'You have already authenticated with Spotify!')

                return HttpResponseRedirect(reverse('moodytunes:spotify-auth-success'))

            # Get access and refresh tokens for user
            spotify_client = SpotifyClient(identifier='spotify_auth_access:{}'.format(user.username))
            tokens = spotify_client.get_access_and_refresh_tokens(code)

            # Get Spotify username from profile data
            profile_data = spotify_client.get_user_profile(tokens['access_token'])

            # Create SpotifyAuth record from data
            try:
                SpotifyUserAuth.objects.get_or_create(
                    user=user,
                    access_token=tokens['access_token'],
                    refresh_token=tokens['refresh_token'],
                    spotify_user_id=profile_data['id']
                )

                logger.info(
                    'Created SpotifyAuthUser record for user {}'.format(user.username),
                    extra={'fingerprint': auto_fingerprint('created_spotify_auth_user', **kwargs)}
                )

                return HttpResponseRedirect(reverse('moodytunes:spotify-auth-success'))
            except IntegrityError:
                logger.exception(
                    'Failed to create auth record for MoodyUser {} with Spotify username {}'.format(
                        user.username,
                        profile_data['id']
                    ),
                    extra={'fingerprint': auto_fingerprint('failed_to_create_spotify_auth_user', **kwargs)}
                )

                messages.error(request, 'Spotify user {} has already authorized MoodyTunes. Please try again'.format(
                    profile_data['id']
                ))

                return HttpResponseRedirect(reverse('moodytunes:spotify-auth-failure'))

        else:
            logger.warning(
                'User {} failed Spotify Oauth confirmation'.format(request.user.username),
                extra={
                    'fingerprint': auto_fingerprint('user_rejected_oauth_confirmation', **kwargs),
                    'error': request.GET['error']
                }
            )

            # Map error code to human-friendly display
            error_messages = {
                'access_denied': 'You rejected to link MoodyTunes to Spotify. Please select Accept next time.'
            }

            messages.error(request, error_messages.get(request.GET['error'], request.GET['error']))

            return HttpResponseRedirect(reverse('moodytunes:spotify-auth-failure'))


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationSuccessView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        messages.info(self.request, 'You have successfully authorized Moodytunes with Spotify!')
        return reverse('moodytunes:export')


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationFailureView(TemplateView):
    template_name = 'spotify_auth_failure.html'


@method_decorator(login_required, name='dispatch')
class ExportPlayListView(FormView):
    template_name = 'export.html'
    form_class = ExportPlaylistForm

    def get(self, request, *args, **kwargs):
        if not SpotifyUserAuth.objects.filter(user=request.user).exists():
            return HttpResponseRedirect(reverse('moodytunes:spotify-auth'))

        return super(ExportPlayListView, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            playlist_name = form.cleaned_data['playlist_name']
            emotion_name = form.cleaned_data['emotion']
            genre = form.cleaned_data['genre']
            context = form.cleaned_data['context']

            songs = ExportPlaylistHelper.get_export_playlist_for_user(request.user, emotion_name, genre, context)

            if not songs:
                emotion = Emotion.objects.get(name=emotion_name)
                emotion_fullname = emotion.full_name
                msg = 'Your {} playlist is empty! Try adding some songs to save the playlist'.format(
                    emotion_fullname.lower()
                )

                messages.error(request, msg)

                return HttpResponseRedirect(reverse('moodytunes:export'))

            auth = get_object_or_404(SpotifyUserAuth, user=request.user)

            CreateSpotifyPlaylistFromSongsTask().delay(auth.id, playlist_name, songs)

            messages.info(request, 'Your playlist has been exported! Check in on Spotify in a little bit to see it')

            return HttpResponseRedirect(reverse('moodytunes:export'))

        else:
            messages.error(request, 'Please submit a valid request')
            return HttpResponseRedirect(reverse('moodytunes:export'))
