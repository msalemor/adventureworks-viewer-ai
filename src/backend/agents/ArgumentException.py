class ArgumentExceptionError(Exception):
    """Exception raised for errors in the arguments."""
    def __init__(self, msg):
        self.msg = msg
