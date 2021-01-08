import functools
import logging
import traceback


class StackInfoHandler(logging.FileHandler):
    log_trim = 6
    middleware_trim = 30

    def emit(self, record):
        super().emit(record)
        stack_before = [str(row) for row in traceback.format_stack()[:-self.log_trim]]
        stack = ''.join(stack_before[self.middleware_trim:])
        self.stream.write(stack)


def update_logging_data(func):
    """Update kwargs with function and class name for fingerprinting"""
    @functools.wraps(func)
    def wrapped(*args, **kwargs):
        cls = args[0]  # Reference to `self` when function is called from a class
        kwargs.update({
            'func_name': func.__name__,
            'class_name': '{}.{}'.format(cls.__module__, cls.__class__.__name__)
        })
        return func(*args, **kwargs)
    return wrapped


def auto_fingerprint(msg, **kwargs):
    """
    Auto format a logging fingerprint with the instance class name and message. Use with
    the `update_logging_data` wrapper to pass in the class and function name as kwargs

    :param msg: (str) Message to insert into fingerprint
    """
    return '{class_name}.{func_name}.{msg}'.format(
        class_name=kwargs.get('class_name', ''),
        func_name=kwargs.get('func_name', ''),
        msg=msg
    )
