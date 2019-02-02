from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.generic.base import TemplateView
from rest_framework import generics

from accounts.forms import CreateUserForm, UpdateUserForm
from accounts.models import MoodyUser
from accounts.serializers import AnalyticsSerializer, AnalyticsRequestSerializer
from base.mixins import GetRequestValidatorMixin
from tunes.models import Emotion
from libs.utils import average


@method_decorator(login_required, name='dispatch')
class ProfileView(TemplateView):
    template_name = 'profile.html'


@method_decorator(login_required, name='dispatch')
class UpdateInfoView(View):
    form_class = UpdateUserForm
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
            messages.info(request, 'Your account information has been updated.')

            # If user changed their password, they need to re-authenticate
            if form.cleaned_data.get('password'):
                messages.info(request, 'Please login with your new password.')

            return HttpResponseRedirect(reverse('accounts:profile'))
        else:
            return render(request, self.template_name, {'form': form})


class CreateUserView(View):
    form_class = CreateUserForm
    template_name = 'create.html'

    def get(self, request):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            user = MoodyUser.objects.create(username=form.cleaned_data['username'])
            user.set_password(form.cleaned_data['password'])
            user.save()

            messages.info(request, 'Your account has been created.')

            return HttpResponseRedirect(reverse('accounts:login'))
        else:
            return render(request, self.template_name, {'form': form})


class AnalyticsView(GetRequestValidatorMixin, generics.RetrieveAPIView):
    serializer_class = AnalyticsSerializer

    get_request_serializer = AnalyticsRequestSerializer

    def get_object(self):
        emotion = Emotion.objects.get(name=self.cleaned_data['emotion'])
        genre = self.cleaned_data.get('genre')

        user_emotion = self.request.user.get_user_emotion_record(emotion.name)
        votes_for_emotion = self.request.user.get_user_song_vote_records(emotion.name)

        energy = user_emotion.energy
        valence = user_emotion.valence

        desired_songs = [vote.song for vote in votes_for_emotion if vote.vote]
        if genre:
            desired_songs = [song for song in desired_songs if song.genre == genre]

        data = {
            'emotion': emotion.name,
            'emotion_name': emotion.full_name,
            'genre': genre,
            'energy': energy,
            'valence': valence,
            'total_songs': len(desired_songs)
        }

        return data
