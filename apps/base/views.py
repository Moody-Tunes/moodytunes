from django.conf import settings
from django.views.generic.base import RedirectView, TemplateView


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        return settings.LOGIN_URL


class FormView(TemplateView):
    """View class for including form on a page"""
    form_class = None

    def get_context_data(self, form_kwargs=None, **kwargs):
        """
        Add an instance of the specified form class to the context dictionary
        :param form_kwargs: (dict) Keyword arguments to pass to the form (if needed)
        :return: (dict) Context dictionary for populating template
        """
        if not form_kwargs:
            form_kwargs = {}

        context = super().get_context_data(**kwargs)
        context['form'] = self.form_class(**form_kwargs)

        return context
