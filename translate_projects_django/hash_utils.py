import hashlib

def base36_encode(number: int) -> str:
    """
    Encodes a number into a Base36 string.
    Args:
        number (int): The number to encode.
    Returns:
        str: The Base36 encoded string.
    """
    chars = "0123456789abcdefghijklmnopqrstuvwxyz"
    result = ""
    while number:
        number, i = divmod(number, 36)
        result = chars[i] + result
    return result or "0"

def generate_short_hash(text: str, length: int = 15) -> str:
    """
    Generates a short hash for a given text using SHA-256 and Base36 encoding.
    Args:
        text (str): The text to hash.
        length (int): The length of the generated hash (default is 15).
    Returns:
        str: The short Base36 hash.
    """
    # Generate SHA-256 hash from the text
    hash_bytes = hashlib.sha256(text.encode()).digest()
    # Convert the hash to an integer
    hash_int = int.from_bytes(hash_bytes, 'big')
    # Convert the integer to Base36
    base36_hash = base36_encode(hash_int)
    # Return a shorter portion of the hash
    return base36_hash[:length]  # Adjust the length here if needed
