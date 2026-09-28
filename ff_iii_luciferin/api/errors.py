class FireflyAPIError(RuntimeError):
    """Error raised for HTTP, network, JSON, or response mapping failures.

    Attributes:
        status_code: HTTP status for an HTTP or JSON response error, or
            ``None`` when no usable HTTP response was received.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
