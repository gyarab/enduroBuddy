from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings


class GarminSecretStoreError(Exception):
    pass


def _load_keys() -> list[str]:
    raw = (getattr(settings, "GARMIN_KMS_KEYS", "") or "").strip()
    keys = [x.strip() for x in raw.split(",") if x.strip()]
    if not keys:
        raise GarminSecretStoreError("GARMIN_KMS_KEYS is not configured.")
    return keys


def _cipher() -> MultiFernet:
    try:
        return MultiFernet([Fernet(k.encode("utf-8")) for k in _load_keys()])
    except Exception as exc:
        raise GarminSecretStoreError("GARMIN_KMS_KEYS is invalid.") from exc


def encrypt_tokenstore(tokenstore: str) -> str:
    if not tokenstore:
        raise GarminSecretStoreError("Tokenstore payload is empty.")
    return _cipher().encrypt(tokenstore.encode("utf-8")).decode("utf-8")


def decrypt_tokenstore(ciphertext: str) -> str:
    if not ciphertext:
        raise GarminSecretStoreError("Encrypted tokenstore payload is empty.")
    try:
        return _cipher().decrypt(ciphertext.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise GarminSecretStoreError("Cannot decrypt Garmin tokenstore with current KMS keys.") from exc
