"""Token encryption at rest.

Generate a key:
    python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
"""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken


class TokenCrypto:
    def __init__(self, fernet_key: str) -> None:
        if not fernet_key:
            raise ValueError("FERNET_KEY is required. Generate one with `townsquare gen-secrets`.")
        self._fernet = Fernet(fernet_key.encode() if isinstance(fernet_key, str) else fernet_key)

    def encrypt(self, plaintext: str) -> bytes:
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes) -> str:
        try:
            return self._fernet.decrypt(ciphertext).decode("utf-8")
        except InvalidToken as e:
            raise ValueError("token decryption failed; check FERNET_KEY rotation") from e
