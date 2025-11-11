from typing import TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.orm.attributes import flag_modified
from sqlalchemy import String, DateTime, event
from sqlalchemy.dialects.postgresql import TIMESTAMP, JSONB
from sqlalchemy.ext.mutable import MutableList
from datetime import datetime
from ..base import date_now
from ..base import Base

import logging.config
from core.logger import logger_config

logging.config.dictConfig(logger_config)
logger = logging.getLogger('model_profile_logger')

if TYPE_CHECKING:
    from .user_association import UserAssociation


class Profile(Base):
    __tablename__ = 'profiles'

    id: Mapped[int] = mapped_column(primary_key=True, index=True, autoincrement=True)
    created_date: Mapped[datetime] = mapped_column(DateTime().with_variant(TIMESTAMP(timezone=True), 'postgresql'))
    visit_date: Mapped[datetime] = mapped_column(DateTime().with_variant(TIMESTAMP(timezone=True), 'postgresql'))
    # COOKIES
    key: Mapped[str] = mapped_column(String(32), unique=True)
    cookie_data: Mapped[MutableList] = mapped_column(MutableList.as_mutable(JSONB), default=lambda: [])
    # PROFILE
    avatar: Mapped[str | None] = mapped_column(String(300))
    # LOCATIONS
    locations: Mapped[MutableList] = mapped_column(MutableList.as_mutable(JSONB), default=lambda: [])
    # IPS & USER-AGENTS
    ip: Mapped[str] = mapped_column(String(45))
    user_agent: Mapped[str] = mapped_column(String(255))
    history: Mapped[MutableList] = mapped_column(MutableList.as_mutable(JSONB), default=lambda: [])
    
    user_association: Mapped['UserAssociation'] = relationship(
        back_populates='profile',
        cascade='all, delete-orphan',
        uselist=False,
        passive_deletes=True
    )

    def add_history(self):
        current_visit = date_now()
        self.visit_date = current_visit
        # Формируем текущее состояние профиля (без changed_at)
        new_state = {
            'ip': self.ip,
            'user_agent': self.user_agent,
            'visit_date': current_visit.isoformat(),
        }
        logger.debug('Текущая история: %s', self.history)
        # Инициализация истории, если она пуста
        if self.history is None:
            self.history = []
        # Флаг, найден ли элемент с таким же ip и user_agent.
        record_found = False
        for entry in self.history:
            if entry.get('ip') == self.ip and entry.get('user_agent') == self.user_agent:
                logger.debug('Обновление существующей записи: %s -> %s', 
                       entry.get('visit_date'), new_state['visit_date'])
                entry.update({
                    'visit_date': new_state['visit_date'],
                })
                record_found = True
                break
        # Если записи с таким ip и user_agent нет, добавляем новую запись
        if not record_found:
            logger.debug('Добавление новой записи: %s', new_state)
            self.history.append(new_state)
            
        flag_modified(self, 'history')
        logger.debug('После обновления профиля: %s', self.history)

# Обработчик события before_update: будем фиксировать состояние Profile перед обновлением.
def before_update_listener(mapper, connection, target: Profile):
    logger.debug('Добавление в историю профиля id=%s', target.id)
    # target — это объект Profile, который обновляется
    target.add_history()

# Регистрируем обработчик события before_update для класса Profile.
event.listen(Profile, 'before_update', before_update_listener)
