from typing import Optional
from jaraco.classes import properties
from keyring.backend import KeyringBackend


class Keyring(KeyringBackend):
    def get_password(self, service: str, username: str) -> Optional[str]:
        if service == "api.example.com" and username == "luser":
            return "hunter2"
        else:
            return None

    def set_password(self, service: str, username: str, password: str) -> None:
        pass

    def delete_password(self, service: str, username: str) -> None:
        pass

    @properties.classproperty
    def priority(self) -> int:
        return 1
