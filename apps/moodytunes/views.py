from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView

from moodytunes.forms import BrowseForm


@method_decorator(login_required, name='dispatch')
class BrowsePlaylistsView(TemplateView):
    template_name = 'browse.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = BrowseForm()

        return context
