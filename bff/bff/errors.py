class ApiError(Exception):
    """Error shown to the user: JSON {"error": message} with the given status."""

    def __init__(self, status: int, message: str, **extra):
        super().__init__(message)
        self.status, self.message, self.extra = status, message, extra
