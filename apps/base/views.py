from django.urls import reverse
from django.views.generic.base import RedirectView, TemplateView


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return reverse('accounts:profile')
        return reverse('accounts:login')


class FormView(TemplateView):
    """View class for including form on a page"""
    form_class = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class()

        return context
