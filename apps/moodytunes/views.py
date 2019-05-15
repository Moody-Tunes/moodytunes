from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from base.views import FormView
from moodytunes.forms import BrowseForm, PlaylistForm


class AboutView(TemplateView):
    template_name = 'about.html'


@method_decorator(login_required, name='dispatch')
class BrowsePlaylistsView(FormView):
    template_name = 'browse.html'
    form_class = BrowseForm


@method_decorator(login_required, name='dispatch')
class EmotionPlaylistsView(FormView):
    template_name = 'playlists.html'
    form_class = PlaylistForm

    def get_context_data(self, **kwargs):
        # Need to pass request user to form for building genre options from votes
        form_kwargs = {'user': self.request.user}

        return super(EmotionPlaylistsView, self).get_context_data(form_kwargs, **kwargs)
