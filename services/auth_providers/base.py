from typing import Protocol


class IdentityProvider(Protocol):
    name: str

    def authenticate(self, username: str, password: str) -> dict | None:
        """Return a stable user identity after successful authentication."""
