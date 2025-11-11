from sqlalchemy.orm import DeclarativeBase
from slugify import slugify
from datetime import datetime
from core.config import settings
import pytz



def date_now() -> datetime:
    """
    Возвращает текущее время в базовом часовом поясе
    в формате '%Y-%m-%d %H:%M:%S %Z'
    """
    base_tz: str = pytz.timezone(settings.location_timezone)
    date_time = datetime.now(base_tz)
    return date_time.replace(microsecond=0)

def generate_slug(string: str, max_length: int) -> str:
    """
    Возвращает slugify строку
    """
    return slugify(
        string,
        max_length=max_length,
        lowercase=True,
        separator='-',
        regex_pattern = r'[^-a-z0-9_]+',
        # stopwords=['the', 'in', 'a', 'hurry'],
        # replacements=[['|', 'or'], ['%', 'percent']],
        )



class Base(DeclarativeBase):
    pass
    # __abstract__ = True

    # @declared_attr.directive
    # def __tablename__(cls) -> str:
    #     return f"{cls.__name__.lower()}s"

    # id: Mapped[int] = mapped_column(primary_key=True)


