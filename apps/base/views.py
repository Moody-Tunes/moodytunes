from django.conf import settings
from django.urls import reverse
from django.views.generic.base import RedirectView, TemplateView


class HomePageView(RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return settings.LOGIN_REDIRECT_URL
        return reverse('landing-page')


class LandingPageView(TemplateView):
    template_name = 'landing_page.html'

    def get_context_data(self, **kwargs):
        context = super(LandingPageView, self).get_context_data(**kwargs)
        context['login_link'] = settings.LOGIN_URL
        context['create_account_link'] = reverse('accounts:create')
        context['about_link'] = reverse('moodytunes:about')

        return context


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
