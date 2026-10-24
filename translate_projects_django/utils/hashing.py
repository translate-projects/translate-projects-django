import hashlib


def base36_encode(number: int) -> str:
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while number:
        number, i = divmod(number, 36)
        result = chars[i] + result
    return result or "0"


def generate_short_hash(text: str, length: int = 15) -> str:
    """SHA-256 → Base36, first `length` chars. Must match the backend's helpers/hash_utils.py byte for byte."""
    hash_int = int.from_bytes(hashlib.sha256(text.encode()).digest(), "big")
    return base36_encode(hash_int)[:length]
