# nefolosite ... inca

class ApplicationError(Exception):
    """Base exception for all application-specific exceptions."""
    pass


class SettingsError(ApplicationError):
    """Raised when loading or saving application settings fails."""
    pass


class CaptureError(ApplicationError):
    """Raised when a screenshot capture operation fails."""
    pass


class WindowError(ApplicationError):
    """Raised when a target window cannot be found or activated."""
    pass


class FileOperationError(ApplicationError):
    """Raised when a file or directory operation fails."""
    pass


class ZipCreationError(ApplicationError):
    """Raised when creating a ZIP archive fails."""
    pass


class ValidationError(ApplicationError):
    """Raised when user input validation fails."""
    pass