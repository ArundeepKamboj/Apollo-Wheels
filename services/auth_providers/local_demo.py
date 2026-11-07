from services.auth import accounts, verify_password


class LocalDemoProvider:
    name = "local"

    def authenticate(self, username: str, password: str) -> dict | None:
        user = next((item for item in accounts()["users"] if item["username"] == username), None)
        if user and verify_password(password, user["salt"], user["password_hash"]):
            return user
        return None
