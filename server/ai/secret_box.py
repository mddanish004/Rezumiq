"""AES-256-GCM seal/open, ported from lib/secret-box.ts."""

from __future__ import annotations

import base64
import hashlib
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from django.conf import settings


def _key() -> bytes:
    secret = os.getenv("AI_KEY_ENCRYPTION_SECRET")
    if secret:
        return hashlib.sha256(secret.encode()).digest()
    base = getattr(settings, "SECRET_KEY", "") or ""
    hkdf = HKDF(algorithm=hashes.SHA256(), length=32, salt=b"", info=b"user-ai-keys")
    return hkdf.derive(base.encode())


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def _unb64u(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def seal(plaintext: str) -> str:
    iv = os.urandom(12)
    aes = AESGCM(_key())
    ct = aes.encrypt(iv, plaintext.encode(), None)
    body = ct[:-16]
    tag = ct[-16:]
    return ".".join(["v1", _b64u(iv), _b64u(tag), _b64u(body)])


def open_sealed(sealed: str) -> str:
    parts = sealed.split(".")
    if len(parts) != 4 or parts[0] != "v1":
        raise ValueError("Unrecognised sealed value")
    _, iv_b, tag_b, body_b = parts
    aes = AESGCM(_key())
    ct = _unb64u(body_b) + _unb64u(tag_b)
    return aes.decrypt(_unb64u(iv_b), ct, None).decode()
