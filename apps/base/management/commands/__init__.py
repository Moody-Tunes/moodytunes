import logging
import uuid

from django.core.management.base import BaseCommand


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
        self.logger = logging.getLogger(self.__class__.__module__)  # Set up logger with name of command module

    def write_to_log_and_output(self, msg, output_stream='stdout', log_level=logging.INFO, extra=None, exc_info=False):
        """
        Write `msg` to both the specified Command output stream, and log at specified `log_level`.

        :param msg: (str) Message to write in output stream and log record
        :param output_stream: (str) Output stream used to write message to console. Must be one of `stdout` or `stderr`
        :param log_level: (int) Log level constant to use in writing message to log
        :param extra: (dict) Extra information to include in log record. Will be updated with the command unique id
        :param exc_info: (bool) Whether or not to include traceback information in log record
        """
        stream = getattr(self, output_stream)
        stream.write(msg)

        if extra is None:
            extra = {}

        extra.update({'command_id': self._unique_id})

        self.logger.log(log_level, msg, extra=extra, exc_info=exc_info)

    def execute(self, *args, **options):
        self.logger.info(
            'Command {name} about to run with {options}. '
            'Identifier: {id}'.format(
                name=self.__class__,
                options=options,
                id=self._unique_id
            )
        )

        return super().execute(*args, **options)
