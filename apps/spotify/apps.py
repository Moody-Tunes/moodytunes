from django.apps import AppConfig


class SpotifyAuthConfig(AppConfig):
    name = 'spotify'

    def ready(self):
        # Register signals
        import spotify.signals  # noqa: F401
