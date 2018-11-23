class SignalDisconnect(object):
    """
    Context manager to disable a signal for a given context. Userful for unit
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
