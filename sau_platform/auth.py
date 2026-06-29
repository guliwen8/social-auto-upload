from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PasswordHash:
    algorithm: str
    iterations: int
    salt_b64: str
    hash_b64: str

    def encode(self) -> str:
        return f"{self.algorithm}${self.iterations}${self.salt_b64}${self.hash_b64}"

    @staticmethod
    def decode(value: str) -> "PasswordHash":
        algo, iters, salt_b64, hash_b64 = value.split("$", 3)
        return PasswordHash(algo, int(iters), salt_b64, hash_b64)


def hash_password(password: str, *, iterations: int = 120_000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations, dklen=32)
    return PasswordHash(
        algorithm="pbkdf2_sha256",
        iterations=iterations,
        salt_b64=base64.b64encode(salt).decode("ascii"),
        hash_b64=base64.b64encode(dk).decode("ascii"),
    ).encode()


def verify_password(password: str, encoded: str) -> bool:
    try:
        parsed = PasswordHash.decode(encoded)
    except Exception:
        return False
    if parsed.algorithm != "pbkdf2_sha256":
        return False
    salt = base64.b64decode(parsed.salt_b64.encode("ascii"))
    expected = base64.b64decode(parsed.hash_b64.encode("ascii"))
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, parsed.iterations, dklen=len(expected)
    )
    return hmac.compare_digest(actual, expected)


def generate_session_token() -> str:
    return "sess_" + secrets.token_urlsafe(32)

