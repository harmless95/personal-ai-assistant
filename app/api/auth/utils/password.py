import bcrypt


class PasswordUtils:
    @staticmethod
    def hash_password(
        password: str,
    ) -> str:
        salt = bcrypt.gensalt()
        pwd_bytes: bytes = password.encode()
        hash_bytes = bcrypt.hashpw(pwd_bytes, salt)
        return hash_bytes.hex()

    @staticmethod
    def validate_password(
        password: str,
        hashed_password: str,
    ) -> bool:
        password_hash = bytes.fromhex(hashed_password)
        return bcrypt.checkpw(
            password=password.encode(),
            hashed_password=password_hash,
        )
