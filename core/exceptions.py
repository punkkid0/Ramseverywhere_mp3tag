class Mp3TagError(Exception):
    """Base exception for MP3 tagging operations."""


class UnsupportedFormatError(Mp3TagError):
    """Raised when the file format is not supported."""


class TagLoadError(Mp3TagError):
    """Raised when tags cannot be read from a file."""


class TagWriteError(Mp3TagError):
    """Raised when tags cannot be written to a file."""


class RemuxError(Mp3TagError):
    """Raised when ffmpeg remux fails."""


class CsvError(Mp3TagError):
    """Raised when CSV operations fail."""