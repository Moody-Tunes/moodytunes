from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View


class HomePageView(View):
    # TODO: See if you can subclass `RedirectView` instead for this
    def get(self, request):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse('accounts:profile'))
        return HttpResponseRedirect(reverse('accounts:login'))
