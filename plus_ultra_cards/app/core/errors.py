class AppError(Exception):
    """Base error with optional context."""
    def __init__(self, message: str, **context):
        super().__init__(message)
        self.context = context

class RenderingError(AppError):
    pass

class RepositoryError(AppError):
    pass

class SrsError(AppError):
    pass

class StudyStateError(AppError):
    pass

