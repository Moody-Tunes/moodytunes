import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import TemplateView
from ratelimit.mixins import RatelimitMixin

from accounts.models import MoodyUser, SpotifyUserAuth
from base.views import FormView
from moodytunes.forms import BrowseForm, PlaylistForm, SuggestSongForm
from moodytunes.tasks import fetch_song_from_spotify
from tunes.utils import CachedPlaylistManager
from libs.spotify import SpotifyClient


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

    def post(self, request, *args, **kwargs):
        # Check if request is rate limited,
        if getattr(request, 'limited', False):
            logger.warning(
                'User {} has been rate limited from suggesting songs'.format(request.user.username),
                extra={'fingerprint': 'rate_limited_suggested_song'}
            )
            messages.error(request, 'You have submitted too many suggestions! Try again in a minute')
            return HttpResponseRedirect(reverse('moodytunes:suggest'))

        form = self.form_class(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']
            fetch_song_from_spotify.delay(code, username=request.user.username)

            logger.info(
                'Called task to add suggestion for song {} by user {}'.format(code, request.user.username),
                extra={'fingerprint': 'added_suggested_song'}
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
                extra={'fingerprint': 'invalid_suggested_song'}
            )
            return render(request, self.template_name, context={'form': form})


class SpotifyAuthenticationView(TemplateView):
    template_name = 'spotify_auth.html'

    def get_context_data(self, **kwargs):
        context = super(SpotifyAuthenticationView, self).get_context_data(**kwargs)

        spotify_client = SpotifyClient()
        context['spotify_auth_url'] = spotify_client.build_spotify_oauth_confirm_link(
            state='user:{}'.format(self.request.user.id),
            scopes=['playlist-modify-private']
        )

        return context


class SpotifyAuthenticationCallbackView(View):

    def get(self, request, *args, **kwargs):
        if 'code' in request.GET:
            code = request.GET['code']
            user = request.user

            # Get access and refresh tokens for user
            spotify_client = SpotifyClient(identifier='spotify_auth_access:{}'.format(user.username))
            tokens = spotify_client.get_access_and_refresh_tokens(code)

            # Get Spotify username from profile data
            profile_data = spotify_client.get_user_profile(tokens['access_token'])

            # Create SpotifyAuth record from data
            SpotifyUserAuth.objects.create(
                user=user,
                access_token=tokens['access_token'],
                refresh_token=tokens['refresh_token'],
                spotify_user_id=profile_data['id']
            )

            logger.info('Created SpotifyAuthUser record for user {}'.format(user.username))

            return HttpResponseRedirect(reverse('moodytunes:spotify-auth-success'))


class SpotifyAuthenticationSuccessView(TemplateView):
    template_name = 'spotify_auth_success.html'


class SpotifyAuthenticationFailureView(View):
    pass
