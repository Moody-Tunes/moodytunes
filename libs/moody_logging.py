import logging
import traceback


class StackInfoHandler(logging.FileHandler):
    log_trim = 6
    middleware_trim = 30

    def emit(self, record):
        super(StackInfoHandler, self).emit(record)
        stack_before = [str(row) for row in traceback.format_stack()[:-self.log_trim]]
        stack = ''.join(stack_before[self.middleware_trim:])
        self.stream.write(stack)


def auto_fingerprint(instance, func_name, msg):
    """
    Auto format a logging fingerprint with the instance class name and message

    :param instance: (class) Class where the log message is derived from
    :param func_name: (str) Name of function that is being called
    :param msg: (str) Message to insert into fingerprint
    """
    return '{module}.{instance_name}.{func_name}.{msg}'.format(
        module=instance.__module__,
        instance_name=instance.__class__.__name__,
        func_name=func_name,
        msg=msg
    )
