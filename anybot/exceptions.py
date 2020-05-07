__all__ = [
    'Error',
    'ApiNotAvailable',
    'ApiError',
    'ActionFailed',
    'NetworkError',
    'TimingError',
]


class Error(Exception):
    pass


class ApiNotAvailable(Error):
    pass


class ApiError(Error, RuntimeError):
    pass


class ActionFailed(ApiError):
    def __init__(self, retcode: int):
        self.retcode = retcode

    def __repr__(self):
        return f'<ActionFailed, retcode={self.retcode}>'

    def __str__(self):
        return self.__repr__()


class NetworkError(Error, IOError):
    pass


class TimingError(Error):
    pass
