import logging
import uuid

from django.core.management.base import BaseCommand

logger = logging.getLogger('mtdj.base.management.commands')


class MoodyBaseCommand(BaseCommand):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unique_id = uuid.uuid4()  # Include in logs for audit trail

    """Override Django core command class to add hooks for our own logic"""
    def execute(self, *args, **options):
        logger.info(
            'Command {name} about to run with {options}. '
            'Identifier: {id}'.format(
            name=self.__class__,
            options=options,
            id=self._unique_id
        ))

        return super().execute(*args, **options)
