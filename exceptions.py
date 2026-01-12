"""Exceptions for HDAnywhere MHUB integration."""


class MHUBException(Exception):
    """Base exception for MHUB integration."""


class MHUBConnectionError(MHUBException):
    """Exception raised when connection to MHUB fails."""


class MHUBTimeoutError(MHUBException):
    """Exception raised when MHUB request times out."""


class MHUBAuthenticationError(MHUBException):
    """Exception raised when authentication fails."""


class MHUBInvalidAPIVersion(MHUBException):
    """Exception raised when API version is not supported."""


class MHUBInvalidResponse(MHUBException):
    """Exception raised when API returns invalid response."""


class MHUBDeviceNotFound(MHUBException):
    """Exception raised when device is not found."""


class MHUBCommandError(MHUBException):
    """Exception raised when command execution fails."""
