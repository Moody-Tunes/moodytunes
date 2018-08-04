from django.db import models


class BaseModel(models.Model):
    """
    Base model that (almost) all models should inherit from. Child models will
    automatically have `created` and `updated` fields included, which denote
    the datetime the record was created and last updated, respectively.
    """
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
