"""Domain-isolated deterministic random streams."""

import hashlib
import random


def stream(seed: int, domain: str) -> random.Random:
    """Derive a stable stream seed using SHA-256 rather than process hash()."""
    digest = hashlib.sha256(f"{seed}:{domain}".encode()).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))
