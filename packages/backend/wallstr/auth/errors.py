class AuthError(Exception):
    """Base class for auth exceptions"""


class EmailAlreadyRegisteredError(AuthError):
    """Raised when an email is already in use."""

    def __init__(self, message: str = "Email already registered") -> None:
        super().__init__(message)


class EmailNotRegisteredError(AuthError):
    """Raised when an email is not registered."""

    def __init__(self, message: str = "Email not registered") -> None:
        super().__init__(message)


class PasswordNotSupportedError(AuthError):
    """Raised when a user has no password."""

    def __init__(self, message: str = "Password not supported") -> None:
        super().__init__(message)


class InvalidPasswordError(AuthError):
    """Raised when a password is incorrect."""

    def __init__(self, message: str = "Invalid password") -> None:
        super().__init__(message)


class TokenExpiredError(AuthError):
    """Raised when a tokend expired."""

    def __init__(self, message: str = "Token expired") -> None:
        super().__init__(message)
