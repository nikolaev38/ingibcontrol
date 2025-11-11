from typing import TYPE_CHECKING
from sqlalchemy import Index, ForeignKey, and_
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


if TYPE_CHECKING:
    from ..role.role import Role
    from .user import WebAppUser, WebSiteUser
    from .profile import Profile

class UserAssociation(Base):
    __tablename__ = 'users_associations'
   
    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    role_id: Mapped[int] = mapped_column(ForeignKey('roles.id', ondelete='CASCADE'))
    profile_id: Mapped[int] = mapped_column(ForeignKey('profiles.id', ondelete='CASCADE'))
    user_website_id: Mapped[int | None] = mapped_column(ForeignKey('website_users.id', ondelete='CASCADE'))
    user_webapp_id: Mapped[int | None] = mapped_column(ForeignKey('webapp_users.id', ondelete='CASCADE'))

    role: Mapped['Role'] = relationship(back_populates='user_associations')
    profile: Mapped['Profile'] = relationship(back_populates='user_association', uselist=False)
    website_user: Mapped['WebSiteUser'] = relationship(back_populates='website_user_association')
    webapp_user: Mapped['WebAppUser'] = relationship(back_populates='webapp_user_association')

    __table_args__ = (
        Index(
            'idx_unique_user_associations', 
            'role_id',
            'profile_id',
            'user_website_id',
            'user_webapp_id',
            unique=True, 
            postgresql_where=and_(
                user_website_id.isnot(None),
                user_webapp_id.isnot(None)
            )
        ),
        Index(
            'idx_website_unique_user_associations', 
            'role_id',
            'profile_id',
            'user_website_id',
            'user_webapp_id',
            unique=True, 
            postgresql_where=user_webapp_id.is_(None)
        ),
        Index(
            'idx_bot_unique_user_associations', 
            'role_id',
            'profile_id',
            'user_website_id',
            'user_webapp_id',
            unique=True, 
            postgresql_where=user_website_id.is_(None)
        ),
    )