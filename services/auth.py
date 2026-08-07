import hmac
import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True)
class SessionUser:
    username: str
    role: str


class AuthService:
    """Small in-memory demo auth boundary; replace with corporate SSO in production."""

    def __init__(self) -> None:
        self.sessions: dict[str, SessionUser] = {}

    @staticmethod
    def _accounts() -> dict[str, tuple[str, str]]:
        return {
            os.getenv("ADMIN_USERNAME", "admin"): (
                os.getenv("ADMIN_PASSWORD", "getnet-demo-admin"),
                "admin",
            ),
            os.getenv("SPECIALIST_USERNAME", "especialista"): (
                os.getenv("SPECIALIST_PASSWORD", "getnet-demo-specialist"),
                "specialist",
            ),
        }

    def login(self, username: str, password: str) -> str | None:
        account = self._accounts().get(username)
        if not account or not hmac.compare_digest(account[0], password):
            return None
        token = secrets.token_urlsafe(32)
        self.sessions[token] = SessionUser(username, account[1])
        return token

    def user(self, token: str | None) -> SessionUser | None:
        return self.sessions.get(token or "")

    def logout(self, token: str | None) -> None:
        if token:
            self.sessions.pop(token, None)
