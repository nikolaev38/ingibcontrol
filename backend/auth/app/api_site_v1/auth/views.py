from typing import List, Optional, Annotated
from fastapi import APIRouter, Depends, status, Response, Cookie, Form, Request
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_fastapi_connect
from core.config import settings

from ..depends import (
    AuthService,
    COOKIES_SESSION_EXCEPTION,
    COOKIES_SESSION_CREATION_EXCEPTION,
    COOKIES_SESSION_UPDATED_EXCEPTION,
    ACCESS_TOKEN_EXCEPTION,
    REFRESH_TOKEN_EXCEPTION,
    PASSWORD_EXCEPTION,
    CHANGE_PASSWORD_EXCEPTION,
    EMAIL_OR_PASSWORD_EXCEPTION,
    EMAIL_CONFLICT_EXCEPTION
)
from core.security import SiteAuthManager
from .dependencies import confirm_email_by_slug, get_client_info
from ..schemas import ReferralData
from pydantic import EmailStr
from annotated_types import MaxLen

# import logging.config
# from core.logger import logger_config

# logging.config.dictConfig(logger_config)
# logger = logging.getLogger('site_endpoints_logger')


router = APIRouter(tags=['Site Auth'])
api_auth = SiteAuthManager()


@router.get('/cookies-session')
async def cookies_session(
    request: Request,
    response: Response,
    session_id: Optional[str] = Cookie(None, include_in_schema=False),
    # Загрузка Cookies session_id через swagger не работает, только через curl
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency)
):
    client_ip, user_agent = get_client_info(request)
    if session_id is None:
        new_session_id = await AuthService.create_cookie_session(
            session=session, client_ip=client_ip, user_agent=user_agent)
        if not new_session_id:
            raise COOKIES_SESSION_CREATION_EXCEPTION
        response.set_cookie(key='session_id', value=new_session_id, httponly=True, path='/')
        session_data = await AuthService.get_cookie_session(session=session, session_id=new_session_id)
        if not session_data:
            raise COOKIES_SESSION_CREATION_EXCEPTION
        return JSONResponse(
            status_code=200,
            content=AuthService.generate_cookies(session_data, 'Session Created', new_session_id)
        )
    # Если cookie передан, проверяем, существует ли сессия
    cookies_session = await AuthService.get_cookie_session(session=session, session_id=session_id)
    if not cookies_session:
        raise COOKIES_SESSION_EXCEPTION
    # Если сессия существует, обновляем её
    updated = await AuthService.update_cookie_session(session=session, session_id=session_id, client_ip=client_ip, user_agent=user_agent)
    if not updated:
        raise COOKIES_SESSION_UPDATED_EXCEPTION
    new_session_id = updated['new_session_id']
    session_data = updated['session']
    response.set_cookie(key='session_id', value=new_session_id, httponly=True, path='/')
    return JSONResponse(
        status_code=200,
        content=AuthService.generate_cookies(session_data, 'Session Updated', new_session_id)
    )


@router.get('/me', status_code=status.HTTP_200_OK)
async def authenticate_user(
    request: Request,
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(AuthService.security)],
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency)
):
    client_ip, user_agent = get_client_info(request)
    user = await AuthService.get_current_user_data(
        session=session, access_token=authorization.credentials,
        client_ip=client_ip, user_agent=user_agent)
    if user:
        response_data = AuthService.generate_ping_info(user)
        return JSONResponse(content=response_data)
    raise ACCESS_TOKEN_EXCEPTION


@router.post('/register', status_code=status.HTTP_201_CREATED)
async def registration(
    request: Request,
    email: Annotated[EmailStr, MaxLen(settings.email_max_len), Form()],
    password: Annotated[str, MaxLen(settings.password_max_len), Form()],
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency)
):  
    client_ip, user_agent = get_client_info(request)
    cookie_session = request.headers.get('Cookie-Session')
    user = await AuthService.user_registration(
        session=session, email=email, password=password,
        client_ip=client_ip, user_agent=user_agent, cookie_session=cookie_session
    )
    if user:
        response_data = AuthService.generate_tokens(user)
        return JSONResponse(content=response_data)
    raise EMAIL_CONFLICT_EXCEPTION


@router.post('/login', status_code=status.HTTP_200_OK)
async def login(
    request: Request,
    email: Annotated[EmailStr, MaxLen(settings.email_max_len), Form()],
    password: Annotated[str, MaxLen(settings.password_max_len), Form()],
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency)
):
    client_ip, user_agent = get_client_info(request)
    cookie_session = request.headers.get('Cookie-Session')
    user = await AuthService.get_user(session=session, email=email)
    if user and SiteAuthManager.validate_password(password, user.password):
        await AuthService.user_login(
            session=session, email=email,
            client_ip=client_ip, user_agent=user_agent, cookie_session=cookie_session
        )
        response_data = AuthService.generate_tokens(user)
        return JSONResponse(content=response_data)
    raise EMAIL_OR_PASSWORD_EXCEPTION


@router.post('/refresh', status_code=status.HTTP_200_OK)
async def refresh(
    request: Request,
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(AuthService.security)],
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency)
):
    client_ip, user_agent = get_client_info(request)
    user = await AuthService.get_current_user(
        session=session, access_token=authorization.credentials,
        client_ip=client_ip, user_agent=user_agent)
    if user:
        response_data = AuthService.generate_tokens(user)
        return JSONResponse(content=response_data)
    raise REFRESH_TOKEN_EXCEPTION


@router.post('/change_password', status_code=status.HTTP_200_OK)
async def change_password(
    request: Request,
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(AuthService.security)],
    current_password: Annotated[str, MaxLen(settings.password_max_len), Form()],
    new_password: Annotated[str, MaxLen(settings.password_max_len), Form()],
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency)
):  
    client_ip, user_agent = get_client_info(request)
    user = await AuthService.get_current_user(
        session=session, access_token=authorization.credentials,
        client_ip=client_ip, user_agent=user_agent)
    if user and SiteAuthManager.validate_password(current_password, user.password):
        user_change_password = await AuthService.user_change_password(
            session=session, email=user.email, new_password=new_password)
        if user_change_password:
            return JSONResponse(jsonable_encoder(user_change_password))
        raise CHANGE_PASSWORD_EXCEPTION
    raise PASSWORD_EXCEPTION


@router.post('/confirm_email/{slug}/', status_code=status.HTTP_200_OK)
async def confirm_email(
    referral: ReferralData = Depends(confirm_email_by_slug),
):  
    return referral