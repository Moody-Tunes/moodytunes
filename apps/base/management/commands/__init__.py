import logging
import uuid

from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class MoodyBaseCommand(BaseCommand):
    """
    Override Django core command class to add hooks for our own logic.

    Each management command in this project should extend this base class and
    take advantage of the unique id instance variable for logging purposes.

    Override the handle() method of your command class to implement your own logic.
    Method signature is `def handle(self, *args, **options)`
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._unique_id = uuid.uuid4()  # Include in logs for audit trail

    def execute(self, *args, **options):
        logger.info(
            'Command {name} about to run with {options}. '
            'Identifier: {id}'.format(
                name=self.__class__,
                options=options,
                id=self._unique_id
            )
        )

        return super().execute(*args, **options)
