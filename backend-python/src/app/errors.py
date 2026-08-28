"""Domain errors.

ONE error type, carrying a stable machine-readable `code`. Services raise it;
the GraphQL layer maps it to an error with `extensions.code` so the frontend can
branch on the code instead of string-matching the message.

Add new failure modes by passing a new code, not a new class:
    raise DomainError("Insufficient funds", code="INSUFFICIENT_FUNDS")
"""


class DomainError(Exception):
    """A rule of the domain was violated. Not a bug — an expected failure."""

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        super().__init__(message)
        self.message = message
        self.code = code
