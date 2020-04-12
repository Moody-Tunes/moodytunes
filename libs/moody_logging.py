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
