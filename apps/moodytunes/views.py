import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

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
        #TODO: Use task to fetch and add song to database
        pass
