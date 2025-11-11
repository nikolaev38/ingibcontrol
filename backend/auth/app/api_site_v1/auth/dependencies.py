from typing import Annotated, Optional, Tuple
from fastapi import Path, Depends, Request, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from core.models import db_fastapi_connect
from ..depends import AuthService


def get_client_info(request: Request) -> Tuple[str, str]:
    """
    Получение IP-адреса и User-Agent из заголовков запроса.
    """
    client_ip = request.headers.get('X-Client-IP') or request.client.host or 'localhost'
    user_agent = request.headers.get('User-Agent', '')
    return client_ip, user_agent

async def confirm_email_by_slug(
    request: Request,
    authorization: Annotated[HTTPAuthorizationCredentials, Depends(AuthService.security)],
    slug: Annotated[str, Path],
    session: AsyncSession = Depends(db_fastapi_connect.scoped_session_dependency),
) -> Optional[bool]:
    client_ip, user_agent = get_client_info(request)
    user = await AuthService.get_current_user(
        session=session, access_token=authorization.credentials,
        client_ip=client_ip, user_agent=user_agent)
    if user:
        answer = await AuthService.confirm_email_by_key(
            session=session, key=slug, email=user.email,
            client_ip=client_ip, user_agent=user_agent)
        if answer is not None:
            return answer

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f'Referral {slug} not found!',
        )
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Incorrect access token')
