"""Custom exceptions for Lyngdorf control library."""


class LyngdorfException(Exception):
    """Base exception for Lyngdorf library."""

    pass


class ConnectionError(LyngdorfException):
    """Connection to device failed or lost."""

    pass


class CommandError(LyngdorfException):
    """Command execution failed."""

    pass


class TimeoutError(LyngdorfException):
    """Command timed out waiting for response."""

    pass


class UnsupportedFeatureError(LyngdorfException):
    """Feature not supported on this model."""

    pass


class InvalidParameterError(LyngdorfException):
    """Invalid parameter value."""

    pass
