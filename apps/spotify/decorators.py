import functools

from django.conf import settings
from django.contrib import messages
from django.http import Http404, HttpResponseRedirect

from spotify.models import SpotifyAuth


def spotify_auth_required(redirect_uri, raise_exc=False):
    """
    Decorator to ensure that the request user has authenticated with Spotify,
    redirecting to the specified URI if they are not.
    """
    def wrapped_view(view_func):
        @functools.wraps(view_func)
        def wrapped(request, *args, **kwargs):
            # Early exit: if the request is not authenticated then redirect to login page
            # (or raise error in the case that an exception should be raised)
            if not request.user.is_authenticated:
                if raise_exc:
                    raise Http404()
                else:
                    return HttpResponseRedirect(settings.LOGIN_URL)
            try:
                auth = SpotifyAuth.objects.get(user=request.user)
                request.spotify_auth = auth  # Cache SpotifyAuth record for request
                return view_func(request, *args, **kwargs)
            except SpotifyAuth.DoesNotExist:
                if raise_exc:
                    raise Http404()
                else:
                    messages.info(request, 'You have not authorized MoodyTunes with Spotify', fail_silently=True)
                    return HttpResponseRedirect(redirect_uri)
        return wrapped
    return wrapped_view
