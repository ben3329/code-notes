from argon2 import PasswordHasher


def hash_password(sha256_password: str) -> str:
    ph = PasswordHasher()
    return ph.hash(sha256_password)


def verify_password(sha256_password: str, hashed_password: str) -> bool:
    ph = PasswordHasher()
    try:
        ph.verify(hashed_password, sha256_password)
        return True
    except:
        return False
