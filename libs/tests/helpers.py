import random
import string

from django.contrib.messages import get_messages

from accounts.models import MoodyUser
from tunes.models import Song, Emotion


def generate_random_unicode_string(length):
    # Generate a random string of non-ascii characters that is `length` characters long
    # From https://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
    # Credit: Jacob Wan

    include_ranges = [
        (0x0021, 0x0021),
        (0x0023, 0x0026),
        (0x0028, 0x007E),
        (0x00A1, 0x00AC),
        (0x00AE, 0x00FF),
        (0x0100, 0x017F),
        (0x0180, 0x024F),
        (0x2C60, 0x2C7F),
        (0x16A0, 0x16F0),
        (0x0370, 0x0377),
        (0x037A, 0x037E),
        (0x0384, 0x038A),
        (0x038C, 0x038C),
    ]

    alphabet = [
        chr(code_point) for current_range in include_ranges
        for code_point in range(current_range[0], current_range[1] + 1)
    ]

    return ''.join(random.choice(alphabet) for _ in range(length))


def get_messages_from_response(response):
    """
    Given a HttpResponse, pull the messages included in the session context from the object
    :param response: (django.HttpResponse) Response returned from a test client call
    :return: (list) Collection of messages from the response
    """
    return [m.message for m in get_messages(response.wsgi_request)]


class SignalDisconnect(object):
    """
    Context manager to disable a signal for a given context. Useful for unit
    testing if you want to test behavior independently of a models signals.

    Example:
    ```
    with SignalDisconnect(post_save, my_signal_method, myModel, my_dispatch_uid):
        # Do work without the signal

    `signal` is a Django Signal objects (post_save, pre_init)
    `method` is the method connected to the signal
    `sender` is the model that calls the connected method
    `my_dispatch_uid` is the unique id attached to the signal
    """

    def __init__(self, signal, method, sender, dispatch_uid):
        self.signal = signal
        self.method = method
        self.sender = sender
        self.dispatch_uid = dispatch_uid

    def __enter__(self):
        self.signal.disconnect(
            self.method,
            sender=self.sender,
            dispatch_uid=self.dispatch_uid
        )

    def __exit__(self, *args):
        self.signal.connect(
            self.method,
            sender=self.sender,
            dispatch_uid=self.dispatch_uid
        )


class MoodyUtil(object):
    """
    Helper class to create and return instances of various model objects
    """
    DEFAULT_USER_PASSWORD = 'test'

    @staticmethod
    def create_song(**kwargs):
        def generate_song_code():
            """Return a mocked Spotify song code"""
            sample = [random.choice(string.ascii_letters) for _ in range(22)]
            code = ''.join(sample)
            return 'spotify:track:{}'.format(code)

        emotion = kwargs.get('emotion') or Emotion.objects.get(name=Emotion.HAPPY)
        energy = kwargs.get('energy') or emotion.energy
        valence = kwargs.get('valence') or emotion.valence

        params = {
            'code': generate_song_code(),
            'name': kwargs.get('name', 'Test Song'),
            'genre': kwargs.get('genre', 'Test Genre'),
            'artist': kwargs.get('artist', 'Test Artist'),
            'energy': energy,
            'valence': valence,
        }

        song, _ = Song.objects.get_or_create(**params)

        return song

    @staticmethod
    def create_user(username='test', password=DEFAULT_USER_PASSWORD, email=None):
        user, _ = MoodyUser.objects.get_or_create(username=username)
        user.set_password(password)

        if email:
            user.email = email

        user.save()

        return user
