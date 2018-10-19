from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.base import TemplateView

from accounts.forms import UpdateUserInfoForm


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'profile.html'


@method_decorator(login_required, name='dispatch')
class UpdateInfoView(View):
    form_class = UpdateUserInfoForm
    template_name = 'update.html'

    def get(self, request):
        initial_data = {
            'username': self.request.user.username,
            'email': self.request.user.email
        }

        form = self.form_class(initial=initial_data)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            request.user.update_information(form.cleaned_data)
            return HttpResponseRedirect(reverse('accounts:update'))
        else:
            # TODO: Handle errors raised by form
            return HttpResponseRedirect(reverse('accounts:update'))
