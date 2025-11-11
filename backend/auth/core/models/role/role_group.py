from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Enum as PgEnum
from enum import Enum

from ..base import Base
from .role_group_association import role_group_role_association

if TYPE_CHECKING:
    from .role import Role

class RoleGroupEnum(Enum):
    CHATS = 'chats'                                 # чаты в Telegram
    GUESTS = 'guests'                               # незарегистрированные пользователи
    USERS = 'users'                                 # пользователи
    ADMINISTRATORS = 'administrators'               # группа администраторов

class RoleGroup(Base):
    __tablename__ = 'roles_groups'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    name: Mapped[RoleGroupEnum] = mapped_column(PgEnum(RoleGroupEnum, name='role_group_enum'), default=RoleGroupEnum.GUESTS, unique=True)
    title_ru: Mapped[str] = mapped_column(String(32))
    description_ru: Mapped[str] = mapped_column(String(255))
    title_en: Mapped[str] = mapped_column(String(32))
    description_en: Mapped[str] = mapped_column(String(255))
    
    roles: Mapped[list['Role']] = relationship(secondary=role_group_role_association, back_populates='group')
