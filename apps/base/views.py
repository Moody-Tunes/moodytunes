from django.urls import reverse
from django.views.generic.base import RedirectView


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse('accounts:profile')
        return reverse('accounts:login')
