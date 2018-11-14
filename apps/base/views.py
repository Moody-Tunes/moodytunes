from django.urls import reverse
from django.views.generic.base import RedirectView

from rest_framework.authentication import SessionAuthentication


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse('accounts:profile')
        return reverse('accounts:login')


class LoginRequiredMixin(object):
    permission_class = SessionAuthentication
