from typing import List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum as PgEnum
from enum import Enum

from ..base import Base
from .role_group_association import role_group_role_association

if TYPE_CHECKING:
    from .role_group import RoleGroup
    from ..user.user_association import UserAssociation

class RoleEnum(Enum):
    CHAT = 'chat'                                   # Чат в Telegram
    GUEST = 'guest'                                 # Незарегистрированный пользователь сайта, или пользователь бота не подтвердивший соглашение об использовании
    
    OWNER = 'owner'                                 # Владелец компании
    USER = 'user'                                   # Стандартный пользователь с минимальной функциональностью
    
    GLOBAL_ADMIN = 'global_admin'                   # Глобальный администратор с полными правами управления платформой
    CONTENT_ADMIN = 'content_admin'                 # Администратор, ответственный за управление и модерацию контента на уровне всей платформы


class Role(Base):
    __tablename__ = 'roles'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[RoleEnum] = mapped_column(PgEnum(RoleEnum, name='role_enum'), default=RoleEnum.GUEST, unique=True)
    title_ru: Mapped[str] = mapped_column(String(32))
    description_ru: Mapped[str] = mapped_column(String(255))
    title_en: Mapped[str] = mapped_column(String(32))
    description_en: Mapped[str] = mapped_column(String(255))
    
    # PgEnum -> прошивается только через List Mapped[List['RoleGroup']], а потом можно поменять Mapped['RoleGroup']
    group: Mapped['RoleGroup'] = relationship(secondary=role_group_role_association, back_populates='roles')
    user_associations: Mapped[List['UserAssociation']] = relationship(back_populates='role')