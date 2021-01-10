import logging

from PIL import Image
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.db import IntegrityError, transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic import RedirectView, TemplateView
from ratelimit.decorators import ratelimit
from spotify_client import SpotifyClient
from spotify_client.exceptions import SpotifyException

from base.views import FormView
from libs.moody_logging import auto_fingerprint, update_logging_data
from spotify.decorators import spotify_auth_required
from spotify.forms import ExportPlaylistForm, SuggestSongForm
from spotify.models import SpotifyAuth
from spotify.tasks import ExportSpotifyPlaylistFromSongsTask, FetchSongFromSpotifyTask
from spotify.utils import ExportPlaylistHelper
from tunes.models import Emotion


logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationView(TemplateView):
    template_name = 'spotify/spotify_auth.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        state = get_random_string(length=settings.SPOTIFY['session_state_length'])

        client = SpotifyClient()
        context['spotify_auth_url'] = client.build_spotify_oauth_confirm_link(
            state,
            settings.SPOTIFY['auth_user_scopes'],
            settings.SPOTIFY['auth_redirect_uri']
        )

        self.request.session['state'] = state
        self.request.session['redirect_url'] = self.request.GET.get('redirect_url')

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
            if SpotifyAuth.objects.filter(user=user).exists():
                messages.info(request, 'You have already authenticated with Spotify!')

                return HttpResponseRedirect(reverse('spotify:spotify-auth-success'))

            # Get access and refresh tokens for user
            spotify_client = SpotifyClient(identifier='spotify_auth_access:{}'.format(user.username))

            try:
                tokens = spotify_client.get_access_and_refresh_tokens(code, settings.SPOTIFY['auth_redirect_uri'])
            except SpotifyException:
                logger.exception(
                    'Unable to get Spotify tokens for user {}'.format(user.username),
                    extra={'fingerprint': auto_fingerprint('failed_get_spotify_tokens', **kwargs)}
                )

                messages.error(request, 'We were unable to retrieve your Spotify profile. Please try again.')
                return HttpResponseRedirect(reverse('spotify:spotify-auth-failure'))

            # Get Spotify username from profile data
            try:
                profile_data = spotify_client.get_user_profile(tokens['access_token'])
            except SpotifyException:
                logger.exception(
                    'Unable to get Spotify profile for user {}'.format(user.username),
                    extra={'fingerprint': auto_fingerprint('failed_get_spotify_profile', **kwargs)}
                )

                messages.error(request, 'We were unable to retrieve your Spotify profile. Please try again.')
                return HttpResponseRedirect(reverse('spotify:spotify-auth-failure'))

            # Create SpotifyAuth record from data
            try:
                with transaction.atomic():
                    auth = SpotifyAuth.objects.create(
                        user=user,
                        access_token=tokens['access_token'],
                        refresh_token=tokens['refresh_token'],
                        spotify_user_id=profile_data['id'],
                        scopes=settings.SPOTIFY['auth_user_scopes'],
                    )

                    logger.info(
                        'Created SpotifyAuth record for user {}'.format(user.username),
                        extra={
                            'fingerprint': auto_fingerprint('created_spotify_auth', **kwargs),
                            'auth_id': auth.pk,
                            'user_id': user.pk,
                            'spotify_user_id': profile_data['id'],
                            'scopes': settings.SPOTIFY['auth_user_scopes'],
                        }
                    )

                    messages.info(request, 'You have successfully authorized Moodytunes with Spotify!')
                    redirect_url = request.session.get('redirect_url') or reverse('spotify:spotify-auth-success')

                    return HttpResponseRedirect(redirect_url)
            except IntegrityError:
                logger.exception(
                    'Failed to create SpotifyAuth record for MoodyUser {} with Spotify username {}'.format(
                        user.username,
                        profile_data['id']
                    ),
                    extra={'fingerprint': auto_fingerprint('failed_to_create_spotify_auth_user', **kwargs)}
                )

                messages.error(request, 'Spotify user {} has already authorized MoodyTunes.'.format(
                    profile_data['id']
                ))

                return HttpResponseRedirect(reverse('spotify:spotify-auth-failure'))

        else:
            logger.warning(
                'User {} failed Spotify Oauth confirmation'.format(request.user.username),
                extra={
                    'fingerprint': auto_fingerprint('user_rejected_oauth_confirmation', **kwargs),
                    'spotify_oauth_error': request.GET['error']
                }
            )

            # Map error code to human-friendly display
            error_messages = {
                'access_denied': 'You rejected to link MoodyTunes to Spotify. Please select Accept next time.'
            }

            messages.error(request, error_messages.get(request.GET['error'], request.GET['error']))

            return HttpResponseRedirect(reverse('spotify:spotify-auth-failure'))


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationSuccessView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        return reverse('spotify:export')


@method_decorator(login_required, name='dispatch')
class SpotifyAuthenticationFailureView(TemplateView):
    template_name = 'spotify/spotify_auth_failure.html'


@method_decorator(spotify_auth_required(reverse_lazy('accounts:profile')), name='dispatch')
@method_decorator(login_required, name='dispatch')
class RevokeSpotifyAuthView(TemplateView):
    template_name = 'spotify/revoke_spotify_auth.html'

    @update_logging_data
    def post(self, request, *args, **kwargs):
        auth = request.spotify_auth
        auth_id = auth.pk
        auth.delete()

        logger.info(
            'Deleted SpotifyAuth for user {}'.format(request.user.username),
            extra={
                'fingerprint': auto_fingerprint('revoked_spotify_auth', **kwargs),
                'auth_id': auth_id
            }
        )

        messages.info(request, 'We have deleted your Spotify data from Moodytunes')
        return HttpResponseRedirect(reverse('accounts:profile'))


@method_decorator(spotify_auth_required(reverse_lazy('spotify:spotify-auth')), name='get')
@method_decorator(spotify_auth_required(reverse_lazy('spotify:spotify-auth'), raise_exc=True), name='post')
@method_decorator(login_required, name='dispatch')
class ExportPlayListView(FormView):
    template_name = 'spotify/export.html'
    form_class = ExportPlaylistForm

    @update_logging_data
    def get(self, request, *args, **kwargs):
        auth = request.spotify_auth

        # Check that user has the proper scopes from Spotify to create playlist
        for scope in settings.SPOTIFY['auth_user_scopes']:
            if not auth.has_scope(scope):
                logger.info(
                    'User {} does not have proper scopes for playlist export. Redirecting to grant scopes'.format(
                        request.user.username
                    ),
                    extra={
                        'user_id': request.user.pk,
                        'auth_id': auth.pk,
                        'scopes': auth.scopes,
                        'expected_scopes': settings.SPOTIFY['auth_user_scopes'],
                        'fingerprint': auto_fingerprint('missing_scopes_for_playlist_export', **kwargs)
                    }
                )

                auth.delete()  # Delete SpotifyAuth record to ensure that it can be created with proper scopes

                messages.info(request, 'Please reauthenticate with Spotify to export your playlist')

                return HttpResponseRedirect(reverse('spotify:spotify-auth'))

        return super().get(request, *args, **kwargs)

    @update_logging_data
    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)

        if form.is_valid():
            auth = request.spotify_auth

            playlist_name = form.cleaned_data['playlist_name']
            emotion_name = form.cleaned_data['emotion']
            genre = form.cleaned_data['genre']
            context = form.cleaned_data['context']

            songs = ExportPlaylistHelper.get_export_playlist_for_user(request.user, emotion_name, genre, context)

            if not songs:
                msg = 'Your {} playlist is empty! Try adding some songs to export the playlist'.format(
                    Emotion.get_full_name_from_keyword(emotion_name).lower()
                )

                messages.error(request, msg)

                return HttpResponseRedirect(reverse('moodytunes:export'))

            # Handle cover image upload
            cover_image_filename = None

            if form.cleaned_data.get('cover_image'):
                cover_image_filename = '{}/{}_{}_{}.jpg'.format(
                    settings.IMAGE_FILE_UPLOAD_PATH,
                    request.user.username,
                    form.cleaned_data['emotion'],
                    form.cleaned_data['playlist_name'],
                )

                img = Image.open(form.cleaned_data['cover_image'])
                img = img.convert('RGB')

                with open(cover_image_filename, 'wb+') as img_file:
                    img.save(img_file, format='JPEG')

            logger.info(
                'Exporting {} playlist for user {} to Spotify'.format(emotion_name, request.user.username),
                extra={
                    'emotion': Emotion.get_full_name_from_keyword(emotion_name),
                    'genre': genre,
                    'context': context,
                    'user_id': request.user.pk,
                    'auth_id': auth.pk,
                    'fingerprint': auto_fingerprint('export_playlist_to_spotify', **kwargs)
                }
            )

            ExportSpotifyPlaylistFromSongsTask().delay(auth.id, playlist_name, songs, cover_image_filename)

            messages.info(request, 'Your playlist has been exported! Check in on Spotify in a little bit to see it')

            return HttpResponseRedirect(reverse('moodytunes:export'))

        else:
            messages.error(request, 'Please submit a valid request')
            return render(request, self.template_name, {'form': form})


@method_decorator(login_required, name='dispatch')
class SuggestSongView(FormView):
    template_name = 'spotify/suggest.html'
    form_class = SuggestSongForm

    @method_decorator(ratelimit(key='user', rate='3/m', method='POST'))
    @update_logging_data
    def post(self, request, *args, **kwargs):
        # Reject request if user is ratelimited
        if request.limited:
            logger.warning(
                'User {} has been rate limited from suggesting songs'.format(request.user.username),
                extra={
                    'fingerprint': auto_fingerprint('rate_limit_suggest_song', **kwargs),
                    'user_id': request.user.id
                }
            )
            messages.error(request, 'You have submitted too many suggestions! Try again in a minute')
            return HttpResponseRedirect(reverse('spotify:suggest'))

        form = self.form_class(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']
            FetchSongFromSpotifyTask().delay(code, username=request.user.username)

            logger.info(
                'Called task to add suggestion for song {} by user {}'.format(code, request.user.username),
                extra={'fingerprint': auto_fingerprint('added_suggested_song', **kwargs)}
            )
            messages.info(request, 'Your song has been slated to be added! Keep an eye out for it in the future')

            return HttpResponseRedirect(reverse('spotify:suggest'))
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
