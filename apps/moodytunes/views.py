import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from accounts.models import UserSuggestedSong
from base.views import FormView
from moodytunes.forms import BrowseForm, PlaylistForm, SuggestSongForm
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
class SuggestSongView(FormView):
    template_name = 'suggest.html'
    form_class = SuggestSongForm

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            code = form.cleaned_data['code']
            UserSuggestedSong.objects.create(user=request.user, code=code)

            logger.info(
                'Saved suggestion for song {} by user {}'.format(code, request.user.username),
                extra={'fingerprint': 'added_suggested_song'}
            )
            messages.info(request, 'Your song has been slated to be added! Keep an eye out for it in the future')

            return HttpResponseRedirect(reverse('moodytunes:suggest'))
        else:
            logger.warning(
                'User {} suggested an invalid song; Errors: {}'.format(
                    request.user.username,
                    form.errors
                ),
                extra={'fingerprint': 'invalid_suggested_song'}
            )
            return render(request, self.template_name, context={'form': form})
