from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Union
from core.config import settings
import bcrypt, jwt, pytz


# Определяем тип для заголовков JWT
JWTHeaders = Dict[str, Any]
JWTPayload = Dict[str, Any]


class SiteAuthManager:
    def __init__(self) -> None:
        self.algorithm: str = settings.auth_jwt.algorithm
        self.tz: timezone = pytz.timezone(settings.location_timezone)
        self.access_token_expire_minutes: int = settings.auth_jwt.access_token_expire_minutes
        self.refresh_token_expire_minutes: int = settings.auth_jwt.refresh_token_expire_minutes
        self.private_key: str = settings.auth_jwt.private_key_path.read_text()
        self.public_key: str = settings.auth_jwt.public_key_path.read_text()

    def _encode_token(
        self,
        head: JWTHeaders,
        payload: JWTPayload,
        expire_minutes: int,
        expire_timedelta: Optional[timedelta] = None,
    ) -> str:
        to_encode = payload.copy()
        now = datetime.now(self.tz)
        if expire_timedelta:
            expire = now + expire_timedelta
        else:
            expire = now + timedelta(minutes=expire_minutes)
        to_encode.update(exp=expire, iat=now)
        encoded = jwt.encode(
            to_encode,
            self.private_key,
            headers=head,
            algorithm=self.algorithm,
        )
        return encoded

    def create_access_token(
        self,
        head: JWTHeaders,
        payload: JWTPayload,
        expire_timedelta: Optional[timedelta] = None,
    ) -> str:
        return self._encode_token(head, payload, self.access_token_expire_minutes, expire_timedelta)

    def create_refresh_token(
        self,
        head: JWTHeaders,
        payload: JWTPayload,
        expire_timedelta: Optional[timedelta] = None,
    ) -> str:
        # Если необходимо, можно добавить дополнительные поля, например, nbf
        return self._encode_token(head, payload, self.refresh_token_expire_minutes, expire_timedelta)

    def decode_token(
        self,
        token: Union[str, bytes],
    ) -> Optional[Dict[str, Any]]:
        try:
            decoded_jwt: Dict[str, Any] = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
            )
        except jwt.ExpiredSignatureError:
            # При истечении срока действия можно вернуть заголовки токена
            decoded_jwt = jwt.get_unverified_header(token)
        except jwt.DecodeError:
            decoded_jwt = None
        return decoded_jwt

    @staticmethod
    def hash_password(password: str) -> str:
        salt = bcrypt.gensalt()
        pwd_bytes = password.encode('utf-8')
        byte_string = bcrypt.hashpw(pwd_bytes, salt)
        return byte_string.decode('utf-8')

    @staticmethod
    def validate_password(password: str, hashed_password: str) -> bool:
        pwd_bytes = password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
