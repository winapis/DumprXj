class DumprXException(Exception):
    pass

class ConfigurationError(DumprXException):
    pass

class DownloadError(DumprXException):
    pass

class ExtractionError(DumprXException):
    pass

class ValidationError(DumprXException):
    pass

class GitOperationError(DumprXException):
    pass

class TelegramError(DumprXException):
    pass