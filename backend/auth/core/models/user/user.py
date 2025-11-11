from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, DateTime
from sqlalchemy.dialects.postgresql import TIMESTAMP
from datetime import datetime
from ..base import Base

if TYPE_CHECKING:
    from .user_association import UserAssociation

class WebSiteUser(Base):
    __tablename__ = 'website_users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(150), unique=True)
    password: Mapped[str] = mapped_column(String(150))
    register_date: Mapped[datetime] = mapped_column(DateTime().with_variant(TIMESTAMP(timezone=True), 'postgresql'))
    activity_date: Mapped[datetime] = mapped_column(DateTime().with_variant(TIMESTAMP(timezone=True), 'postgresql'))
    email_confirm: Mapped[bool] = mapped_column(default=False)
    
    website_user_association: Mapped['UserAssociation'] = relationship(back_populates='website_user')

class WebAppUser(Base):
    __tablename__ = 'webapp_users'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    
    webapp_user_association: Mapped['UserAssociation'] = relationship(back_populates='webapp_user',  uselist=False)


# class MobileAppUser(Base):
#     pass