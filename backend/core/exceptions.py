"""
Custom Exception Classes
"""

class APIError(Exception):
    """Base API exception"""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class DatabaseError(APIError):
    """Database operation error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class PipelineError(APIError):
    """Pipeline operation error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class ServiceError(APIError):
    """Service operation error"""
    def __init__(self, message: str, status_code: int = 500):
        super().__init__(message, status_code)


class ModelError(APIError):
    """ML model error"""
    def __init__(self, message: str):
        super().__init__(message, status_code=503)