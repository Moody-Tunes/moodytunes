import logging

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from base.views import FormView
from moodytunes.forms import BrowseForm, PlaylistForm
from tunes.utils import CachedPlaylistManager


logger = logging.getLogger(__name__)


class AboutView(TemplateView):
    template_name = 'about.html'


@method_decorator(login_required, name='dispatch')
class BrowsePlaylistsView(FormView):
    template_name = 'browse.html'
    form_class = BrowseForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Check if user has a cached browse playlist to retrieve
        cached_playlist_manager = CachedPlaylistManager(self.request.user)
        cached_playlist = cached_playlist_manager.retrieve_cached_browse_playlist()
        context['cached_playlist_exists'] = cached_playlist is not None

        return context


@method_decorator(login_required, name='dispatch')
class EmotionPlaylistsView(FormView):
    template_name = 'playlists.html'
    form_class = PlaylistForm
