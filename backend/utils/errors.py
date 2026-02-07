"""
Custom exception hierarchy for the Audio Mastering Tool.

All application-specific exceptions inherit from ``AudioMasteringError``
so that callers can catch the base class for broad error handling.
"""


class AudioMasteringError(Exception):
    """Base exception for all Audio Mastering Tool errors."""

    def __init__(self, message: str = "An audio mastering error occurred") -> None:
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        return self.message


class DatabaseError(AudioMasteringError):
    """Raised when a database operation fails."""

    def __init__(self, message: str = "A database error occurred") -> None:
        super().__init__(message)


class ValidationError(AudioMasteringError):
    """Raised when input validation fails."""

    def __init__(self, message: str = "Validation error") -> None:
        super().__init__(message)


class FileNotFoundError(AudioMasteringError):
    """Raised when an expected audio file cannot be located."""

    def __init__(self, message: str = "File not found") -> None:
        super().__init__(message)


class AnalysisError(AudioMasteringError):
    """Raised when the DSP analysis pipeline encounters an error."""

    def __init__(self, message: str = "Analysis failed") -> None:
        super().__init__(message)
