from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from base.views import FormView
from moodytunes.forms import BrowseForm, PlaylistForm


@method_decorator(login_required, name='dispatch')
class BrowsePlaylistsView(FormView):
    template_name = 'browse.html'
    form_class = BrowseForm

@method_decorator(login_required, name='dispatch')
class EmotionPlaylistsView(FormView):
    template_name = 'playlists.html'
    form_class = PlaylistForm
