import random
import string

from accounts.models import MoodyUser
from tunes.models import Song, Emotion


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
    def create_song(name='Test Song', artist='Test Artist', genre='Test Genre', emotion=None, energy=None, valence=None):
        def generate_song_code():
            """Return a mocked Spotify song code"""
            sample = [random.choice(string.ascii_letters) for _ in range(22)]
            code = ''.join(sample)
            return 'spotify:track:{}'.format(code)

        emotion = emotion or Emotion.objects.get(name=Emotion.HAPPY)
        energy = energy or emotion.energy
        valence = valence or emotion.valence

        params = {
            'code': generate_song_code(),
            'name': name,
            'genre': genre,
            'artist': artist,
            'energy': energy,
            'valence': valence,
        }

        song, _ = Song.objects.get_or_create(**params)

        return song

    @staticmethod
    def create_user(username='test', password=DEFAULT_USER_PASSWORD):
        user, _ = MoodyUser.objects.get_or_create(username=username)
        user.set_password(password)
        user.save()

        return user
