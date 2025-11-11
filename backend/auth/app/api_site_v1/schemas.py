from typing import Annotated, Optional, List
from annotated_types import MaxLen
from pydantic import BaseModel, EmailStr
from datetime import datetime
from core.config import settings


class ValidateEmail(BaseModel):
    email: Annotated[EmailStr, MaxLen(settings.email_max_len)]

class ValidatePassword(BaseModel):
    password: Annotated[str, MaxLen(settings.password_max_len)]

class UserRegistered(BaseModel):
    email: str
    role_id: int

class UserLoginRegistered(UserRegistered):
    password: str

class UserChangePassword(BaseModel):
    email: str

class AuthInfo(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class PingAuthInfo(BaseModel):
    id: int
    email: str
    email_confirm: bool
    role: str
    g_roles: str
    avatar: str | None
    activity_date: datetime | None

class RefreshAuth(BaseModel):
    id: int
    email: str
    email_confirm: bool
    group_id: str
    role: str
    avatar: str | None
    activity_date: datetime | None
    access_token: str
    refresh_token: str

class ReferralData(BaseModel):
    key: Annotated[str, MaxLen(settings.referral_key_max_len)]

class CookiesData(BaseModel):
    user_id: Optional[int]
    name: str
    custom_data: str

class CookiesUpdate(BaseModel):
    new_session_id: str
    session: str

class CookiesResponse(BaseModel):
    user: CookiesData
    message: str
    new_session_id: str
