from django.conf import settings
from django.contrib import messages
from django.views.generic.base import RedirectView, TemplateView


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        return settings.LOGIN_URL


class PasswordResetDone(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        messages.info(self.request, 'Please login with your new password')
        return settings.LOGIN_URL


class FormView(TemplateView):
    """View class for including form on a page"""
    form_class = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()

        return context
