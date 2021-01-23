from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.views.generic.base import RedirectView, TemplateView
from rest_framework import status


def not_found_handler(request, exception):
    return render(request, 'mtdj_404.html', status=status.HTTP_404_NOT_FOUND)


def server_error_handler(request):
    return render(request, 'mtdj_500.html', status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        return reverse('landing-page')


class LandingPageView(TemplateView):
    template_name = 'landing_page.html'


class FormView(TemplateView):
    """View class for including form on a page"""
    form_class = None

    def get_form_instance(self):
        """
        Return an instance of the specified form class.
        Override this method if you need to pass any arguments to your form class constructor.
        """
        return self.form_class()

    def get_context_data(self, **kwargs):
        """Add an instance of the specified form class to the context dictionary"""
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form_instance()

        return context
