from typing import Optional
from fastapi import HTTPException, status
from fastapi.encoders import jsonable_encoder 
from fastapi.security import HTTPBearer
from core.security import SiteAuthManager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload
from core.models import (
    Role, WebSiteUser,
    Profile,
    UserAssociation,
)
from core.models.role.role import RoleEnum
from core.models.base import date_now
from .schemas import (
    UserLoginRegistered,
    UserRegistered,
    UserChangePassword,
    AuthInfo,
    PingAuthInfo,
    CookiesData,
    CookiesUpdate,
    CookiesResponse
)
import uuid

import logging.config
from core.logger import logger_config

logging.config.dictConfig(logger_config)
logger = logging.getLogger('site_auth_repository_logger')


# Определяем исключения
CRED_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail='Credentials are not valid'
)
ROLE_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail='This feature is only available to admins'
)
EXPIRED_EXCEPTION = HTTPException(
    status_code=status.HTTP_403_FORBIDDEN, detail='Signature has expired'
)
DATA_EXCEPTION = HTTPException(
    status_code=status.HTTP_404_NOT_FOUND, detail='User not found'
)
ACCESS_TOKEN_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect access token'
)
REFRESH_TOKEN_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect refresh token'
)
COOKIES_SESSION_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid session'
)
PASSWORD_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect password'
)
EMAIL_OR_PASSWORD_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect email or password'
)
EMAIL_CONFLICT_EXCEPTION = HTTPException(
    status_code=status.HTTP_409_CONFLICT, detail='The email is already stored'
)
COOKIES_SESSION_CREATION_EXCEPTION = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Session creation error'
)
COOKIES_SESSION_UPDATED_EXCEPTION = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='Session updated error'
)
CHANGE_PASSWORD_EXCEPTION = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail='An unexpected error occurred'
)



class AuthService:
    class JWTKeys:
        ACCESS = 'accessToken'
        REFRESH = 'refreshToken'
    
    security: HTTPBearer = HTTPBearer()
    api_auth: SiteAuthManager = SiteAuthManager()


    @classmethod
    def generate_key_32(cls) -> str:
        return uuid.uuid4().hex[:32]
    
    @classmethod
    async def create_cookie_session(
        cls,
        session: AsyncSession,
        client_ip: str,
        user_agent: str
    ) -> Optional[str]:
        cookie_data = {
            'user_id': None,
            'name': 'Иван',
            'custom_data': 'new'
        }
        try:
            async with session.begin_nested():
                result = await session.execute(
                    select(Role.id).where(Role.name == RoleEnum.GUEST)
                )
                role_id = result.scalar_one()
                key = cls.generate_key_32()
                profile = Profile(
                    key=key,
                    cookie_data=[cookie_data],
                    ip=client_ip,
                    user_agent=user_agent,
                    created_date=date_now(),
                    visit_date=date_now()
                )
                session.add(profile)
                await session.flush()
                association = UserAssociation(
                    role_id=role_id,
                    profile=profile
                )
                session.add(association)
            await session.commit()
            logger.debug('Создана cookie сессия с ID: %s', key)
            return key
        except IntegrityError as e:
            await session.rollback()
            logger.error('Интеграционная ошибка: %s', e)
            return None
        except Exception as e:
            await session.rollback()
            logger.error('Исключение, ошибка: %s', e)
            return None

    @classmethod
    async def get_cookie_session(cls, session: AsyncSession, session_id: str) -> Optional[CookiesData]:
        result = await session.execute(
                select(Profile.cookie_data).where(Profile.key == session_id)
            )
        cookie_data = result.scalar_one_or_none()
        if not cookie_data:
            logger.error('Не найдена cookie сессия, session_id: %s', session_id)
        return cookie_data[0] if cookie_data else None

    @classmethod
    async def update_cookie_session(
        cls,
        session: AsyncSession,
        session_id: str,
        client_ip: str,
        user_agent: str
    ) -> Optional[CookiesUpdate]:
        try:
            async with session.begin_nested():
                result = await session.execute(
                        select(Profile).where(Profile.key == session_id)
                    )
                profile = result.scalar_one()
                if not profile or not profile.cookie_data:
                    raise COOKIES_SESSION_EXCEPTION
                session_data = profile.cookie_data[0]
                session_data['custom_data'] = 'updated'
                session_data['name'] = session_data['name'] + '_new'
                # Обновляем запись непосредственно в модели
                profile.cookie_data[0] = session_data
                await cls._update_profile(profile, client_ip, user_agent)
            await session.commit()
            return {'new_session_id': session_id, 'session': session_data}
        except IntegrityError as e:
            await session.rollback()
            logger.error('Интеграционная ошибка: %s', e)
            return None
        except Exception as e:
            await session.rollback()
            logger.error('Исключение, ошибка: %s', e)
            return None
    
    @classmethod
    def generate_cookies(cls, session_data: dict, message: str, new_session_id: str) -> CookiesResponse:
        cookies_response = CookiesResponse(
            user=CookiesData(**session_data),
            message=message,
            new_session_id=new_session_id
        )
        return jsonable_encoder(cookies_response)
    
    @classmethod
    async def _update_profile(
        cls,
        profile: Profile,
        client_ip: str,
        user_agent: str,
        cookie_data: CookiesData = None
    ) -> None:
        """
        Обновление профиля пользователя.
        """
        profile.ip = client_ip
        profile.user_agent = user_agent
        profile.visit_date = date_now()
        
        if cookie_data:
            profile.cookie_data = cookie_data

    @classmethod
    async def confirm_email_by_key(
        cls,
        session: AsyncSession,
        key: str,
        email: str,
        client_ip: str,
        user_agent: str
    ) -> Optional[bool]:
        stmt = (
            select(WebSiteUser)
            .options(
                joinedload(WebSiteUser.website_user_association)
                .joinedload(UserAssociation.profile)
            )
            .where(WebSiteUser.email == email)
            .where(
                WebSiteUser.website_user_association.has(
                    UserAssociation.profile.has(Profile.key == key)
                )
            )
        )
        result = await session.execute(stmt)
        website_user = result.scalar_one_or_none()
        if website_user:
            if not website_user.email_confirm:
                try:
                    # Используем вложенную транзакцию
                    async with session.begin_nested():
                        await session.execute(update(WebSiteUser).where(
                            WebSiteUser.id == website_user.id).values(
                                activity_date=date_now(),
                                email_confirm=True))
                        profile = await session.get(Profile, website_user.website_user_association.profile_id)
                        await cls._update_profile(profile, client_ip, user_agent)
                    await session.commit()
                    return True
                except IntegrityError as e:
                    await session.rollback()
                    logger.error('Интеграционная ошибка: %s', e)
                    return False
                except Exception as e:
                    await session.rollback()
                    logger.error('Исключение, ошибка: %s', e)
                    return False
            else:
                return False
        return None

    @classmethod
    async def user_registration(
        cls,
        session: AsyncSession,
        email: str,
        password: str,
        client_ip: str,
        user_agent: str,
        cookie_session: Optional[str],
    ) -> Optional[UserRegistered]:
        """
        Обработка регистрации пользователя на сайте.
        """
        try:
            # Используем вложенную транзакцию
            async with session.begin_nested():
                result_role = await session.execute(
                    select(Role.id).where(Role.name == RoleEnum.USER)
                )
                role_id = result_role.scalar_one()
                if cookie_session and await cls.get_cookie_session(session, cookie_session):
                    result_profile = await session.execute(
                        select(Profile)
                        .options(
                            joinedload(Profile.user_association)
                        )
                        .where(Profile.key == cookie_session)
                    )
                    profile = result_profile.scalar_one_or_none()
                    key = profile.key
                    if not profile:
                        logger.error('Ошибка поиска профиля cookie_session: %s', cookie_session)
                        raise COOKIES_SESSION_EXCEPTION
                    user_website = WebSiteUser(
                        email=email,
                        password=SiteAuthManager.hash_password(password),
                        register_date=date_now(),
                        activity_date=date_now(),
                    )
                    session.add(user_website)
                    await session.flush()
                    await session.execute(update(UserAssociation).where(
                        UserAssociation.id == profile.user_association.id).values(
                            role_id=role_id,
                            user_website_id=user_website.id))
                else:
                    key = cls.generate_key_32()
                    user_website = WebSiteUser(
                        email=email,
                        password=SiteAuthManager.hash_password(password),
                        register_date=date_now(),
                        activity_date=date_now(),
                    )
                    session.add(user_website)
                    await session.flush()
                    profile = Profile(
                        key=key,
                        ip=client_ip,
                        user_agent=user_agent,
                        created_date=date_now(),
                        visit_date=date_now()
                    )
                    session.add(profile)
                    await session.flush()
                    association = UserAssociation(
                        role_id=role_id,
                        profile=profile,
                        user_website_id=user_website.id,
                    )
                    session.add(association)
            await session.commit()
            return UserRegistered(email=user_website.email, role_id=role_id)
        except IntegrityError as e:
            await session.rollback()
            logger.error('Интеграционная ошибка: %s', e)
            return None
        except Exception as e:
            await session.rollback()
            logger.error('Исключение, ошибка: %s', e)
            return None

    @classmethod
    async def user_change_password(
        cls,
        session: AsyncSession,
        email: str,
        new_password: str
    ) -> Optional[UserChangePassword]:
        try:
            # Используем вложенную транзакцию
            async with session.begin_nested():
                await session.execute(update(WebSiteUser).where(
                    WebSiteUser.email == email).values(
                        password=SiteAuthManager.hash_password(new_password)))
            await session.commit()
            return UserChangePassword(email=email)
        except IntegrityError as e:
            await session.rollback()
            logger.error('Интеграционная ошибка: %s', e)
            return None
        except Exception as e:
            await session.rollback()
            logger.error('Исключение, ошибка: %s', e)
            return None

    @classmethod
    async def get_user(
        cls,
        session: AsyncSession,
        email: str,
    ) -> Optional[UserLoginRegistered]:
        query = (
            select(WebSiteUser)
            .options(
                joinedload(WebSiteUser.website_user_association)
            )
            .where(WebSiteUser.email == email)
            )
        sql_result = await session.execute(query)
        user_website = sql_result.scalars().one_or_none()
        if user_website is None:
            return None
        return UserLoginRegistered(
            email=user_website.email,
            role_id=user_website.website_user_association.role_id,
            password=user_website.password)

    @classmethod
    async def user_login(
        cls,
        session: AsyncSession,
        email: str,
        client_ip: str,
        user_agent: str,
        cookie_session: Optional[str] = None,
    ) -> Optional[UserLoginRegistered]:
        """
        Обработка входа на сайт по email и password.
        """
        try:
            # Используем вложенную транзакцию
            async with session.begin_nested():
                query = (
                    select(WebSiteUser)
                    .options(
                        joinedload(WebSiteUser.website_user_association)
                        .joinedload(UserAssociation.profile)
                    )
                    .where(WebSiteUser.email == email)
                    )
                sql_result = await session.execute(query)
                user_website = sql_result.scalars().one()
                if cookie_session and await cls.get_cookie_session(session, cookie_session):
                    if user_website.website_user_association.profile.key != cookie_session:
                        sql_temporary_profile = (
                            select(Profile)
                            .options(
                                joinedload(Profile.user_association)
                            )
                            .where(Profile.key == cookie_session)
                        )
                        temporary_profile_result = await session.execute(sql_temporary_profile)
                        temporary_profile = temporary_profile_result.scalars().one()
                        if not temporary_profile.user_association.user_website_id:
                            await session.delete(temporary_profile)
                        else:
                            logger.debug('Найден нестандартный профиль UserAssociation - id:%s', temporary_profile.user_association.id)
                await session.execute(update(WebSiteUser).where(
                    WebSiteUser.id == user_website.id).values(
                        activity_date=date_now()))
                profile = await session.get(Profile, user_website.website_user_association.profile_id)
                await cls._update_profile(profile, client_ip, user_agent)
            await session.commit()
            return UserLoginRegistered(
                email=user_website.email,
                role_id=user_website.website_user_association.role_id,
                password=user_website.password)
        except IntegrityError as e:
            await session.rollback()
            logger.error('Интеграционная ошибка: %s', e)
            return None
        except Exception as e:
            await session.rollback()
            logger.error('Исключение, ошибка: %s', e)
            return None

    @classmethod
    async def user_get_data(
        cls,
        session: AsyncSession,
        email: str,
        client_ip: str,
        user_agent: str
    ) -> Optional[PingAuthInfo]:
        """
        Загрузка данных зарегистрированного пользователя.
        """
        try:
            # Используем вложенную транзакцию
            async with session.begin_nested():
                query = (
                    select(WebSiteUser)
                    .options(joinedload(WebSiteUser.website_user_association)
                        .joinedload(UserAssociation.role)
                        .joinedload(Role.group))
                    .options(joinedload(WebSiteUser.website_user_association)
                        .joinedload(UserAssociation.profile))
                    .options(joinedload(WebSiteUser.website_user_association)
                        .joinedload(UserAssociation.webapp_user))
                    .where(WebSiteUser.email == email)
                    )
                sql_result = await session.execute(query)
                user_website = sql_result.scalars().one_or_none()
                if user_website is None:
                    return None
                await session.execute(update(WebSiteUser).where(
                    WebSiteUser.id == user_website.id).values(
                        activity_date=date_now()))
                profile = await session.get(Profile, user_website.website_user_association.profile_id)

                await cls._update_profile(profile, client_ip, user_agent)
            await session.commit()
            return PingAuthInfo(
                id=user_website.website_user_association.profile.id,
                email=user_website.email,
                email_confirm=user_website.email_confirm,
                role=user_website.website_user_association.role.name,
                g_roles=user_website.website_user_association.role.group.name,
                avatar=user_website.website_user_association.profile.avatar,
                activity_date=user_website.activity_date)
        except IntegrityError as e:
            await session.rollback()
            logger.error('Интеграционная ошибка: %s', e)
            return None
        except Exception as e:
            await session.rollback()
            logger.error('Исключение, ошибка: %s', e)
            return None
        
    @classmethod
    def generate_tokens(cls, user: UserRegistered) -> AuthInfo:
        """
        Создает access и refresh токены для пользователя и возвращает
        закодированный JSON-словарь с данными авторизации.
        """
        access_token = cls.api_auth.create_access_token(
            head={'iss': cls.JWTKeys.ACCESS},
            payload={
                'rol': user.role_id,
                'sub': user.email
            }
        )
        refresh_token = cls.api_auth.create_refresh_token(
            head={'iss': cls.JWTKeys.REFRESH},
            payload={
                'rol': user.role_id,
                'sub': user.email
            }
        )
        auth_info = AuthInfo(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type='Bearer'
        )
        return jsonable_encoder(auth_info)
    
    @classmethod
    def generate_ping_info(cls, user: PingAuthInfo) -> PingAuthInfo:
        """
        Подготовка данных зарегистрированного пользователя для отправки.
        """
        ping_data_info = PingAuthInfo(
            id=user.id,
            email=user.email,
            email_confirm=user.email_confirm,
            role=user.role,
            g_roles=user.g_roles,
            avatar=user.avatar,
            activity_date=user.activity_date,
        )
        return jsonable_encoder(ping_data_info)
    
    @classmethod
    async def get_current_user(
        cls,
        session: AsyncSession,
        access_token: str,
        client_ip: str,
        user_agent: str
    ) -> Optional[UserLoginRegistered]:
        """
        Извлекаем текущего аутентифицированного пользователя.
        При ошибках декодирования токена или отсутствии пользователя выбрасывается HTTPException.
        Возвращаем UserLoginRegistered.
        """
        payload = cls.api_auth.decode_token(access_token)
        if payload is None:
            raise CRED_EXCEPTION
        if payload.get('sub') is None:
            raise EXPIRED_EXCEPTION

        email: str = payload.get('sub')
        if email is None:
            raise CRED_EXCEPTION

        user = await cls.user_login(
            session=session, email=email,
            client_ip=client_ip, user_agent=user_agent
        )
        if user is None:
            raise DATA_EXCEPTION
        return user

    @classmethod
    async def get_current_user_data(
        cls,
        session: AsyncSession,
        access_token: str,
        client_ip: str,
        user_agent: str
    ) -> Optional[PingAuthInfo]:
        """
        Извлекаем текущего аутентифицированного пользователя.
        При ошибках декодирования токена или отсутствии пользователя выбрасывается HTTPException.
        Возвращаем PingAuthInfo.
        """
        payload = cls.api_auth.decode_token(access_token)
        if payload is None:
            raise CRED_EXCEPTION
        if payload.get('sub') is None:
            raise EXPIRED_EXCEPTION

        email: str = payload.get('sub')
        if email is None:
            raise CRED_EXCEPTION

        user = await cls.user_get_data(
            session=session, email=email,
            client_ip=client_ip, user_agent=user_agent
        )
        if user is None:
            raise DATA_EXCEPTION
        return user
    
    @classmethod
    async def get_current_admin(
        cls,
        session: AsyncSession,
        access_token: str,
        client_ip: str,
        user_agent: str
    ) -> Optional[UserLoginRegistered]:
        """
        Извлекаем текущего аутентифицированного пользователя с проверкой административных прав.
        Если роль пользователя не равна 1 (предполагается, что admin имеет role_id==1), выбрасывается ROLE_EXCEPTION.
        """
        payload = cls.api_auth.decode_token(access_token)
        if payload is None:
            raise CRED_EXCEPTION
        if payload.get('sub') is None:
            raise EXPIRED_EXCEPTION

        email: str = payload.get('sub')
        role_id: int = payload.get('rol')
        if role_id != 1:
            raise ROLE_EXCEPTION
        if email is None:
            raise CRED_EXCEPTION

        user = await cls.user_login(
            session=session, email=email,
            client_ip=client_ip, user_agent=user_agent
        )
        if user is None:
            raise DATA_EXCEPTION
        return user
