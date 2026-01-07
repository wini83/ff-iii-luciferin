class FireflyAPIError(RuntimeError):
    """Raised when Firefly III API calls fail."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
