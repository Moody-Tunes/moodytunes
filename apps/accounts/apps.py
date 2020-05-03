from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        # Register signals
        import accounts.signals  # noqa: F401
        import pdb; pdb.set_trace()