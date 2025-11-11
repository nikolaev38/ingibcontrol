#!/usr/bin/env python3
import sys
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

# Затем добавляем путь к системным пакетам
sys.path.append('/usr/local/lib/python3.12/site-packages')


from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from core.config import settings
from core.models.role.role_group import RoleGroup, RoleGroupEnum
from core.models.role.role import Role, RoleEnum

class UserManagementService:
    """
    Сервис для управления пользователями, ролями и группами ролей.
    """
    
    def __init__(self, db_session: Session):
        self.db_session = db_session

    def create_role_group(self, 
                         name: RoleGroupEnum, 
                         title_ru: str, 
                         description_ru: str,
                         title_en: str, 
                         description_en: str) -> RoleGroup:
        """
        Создает группу ролей с указанным именем и описанием.
        Если группа с таким именем уже существует, возвращает её.
        """
        role_group = self.db_session.query(RoleGroup).filter_by(name=name).first()
        if role_group:
            print(f"Role group '{name}' already exists, skipping creation")
            return role_group

        role_group = RoleGroup(
            name=name, 
            title_ru=title_ru, 
            description_ru=description_ru, 
            title_en=title_en, 
            description_en=description_en
        )
        self.db_session.add(role_group)
        try:
            self.db_session.commit()
            print(f"Created role group: {name}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error creating role group {name}: {e}")
            raise

        return role_group

    def create_role(self, 
                   name: RoleEnum,
                   title_ru: str, 
                   description_ru: str,
                   title_en: str, 
                   description_en: str,
                   group: RoleGroup = None) -> Role:
        """
        Создает новую роль с указанным именем и описанием.
        Если роль с таким именем уже существует, возвращает её.
        """
        role = self.db_session.query(Role).filter_by(name=name).first()
        if role:
            print(f"Role '{name}' already exists, skipping creation")
            return role

        role = Role(
            name=name, 
            title_ru=title_ru, 
            description_ru=description_ru, 
            title_en=title_en, 
            description_en=description_en
        )
        
        if group:
            role.group = group

        self.db_session.add(role)
        try:
            self.db_session.commit()
            print(f"Created role: {name}")
        except SQLAlchemyError as e:
            self.db_session.rollback()
            print(f"Error creating role {name}: {e}")
            raise

        return role

def init_roles():
    # Настройка подключения к базе данных
    sync_engine = create_engine(url=settings.db.sync_url, echo=False, pool_size=5, max_overflow=10)
    SessionLocal = sessionmaker(autoflush=False, bind=sync_engine)
    session = SessionLocal()
    
    try:
        service = UserManagementService(session)
        
        print("="*50)
        print("Инициализация ролей...")
        print("="*50)
        
        # 1. Создание групп ролей
        print("\nСоздание групп ролей...")
        admin_group = service.create_role_group(
            name=RoleGroupEnum.ADMINISTRATORS,
            title_ru='Администраторы',
            description_ru='Группа администраторов платформы.',
            title_en='Administrators',
            description_en='Group of platform administrators.'
        )
        
        users_group = service.create_role_group(
            name=RoleGroupEnum.USERS,
            title_ru='Пользователи',
            description_ru='Группа зарегистрированных пользователей',
            title_en='Users',
            description_en='Group of registered users'
        )
        
        guests_group = service.create_role_group(
            name=RoleGroupEnum.GUESTS,
            title_ru='Гости',
            description_ru='Группа незарегистрированных пользователей',
            title_en='Guests',
            description_en='Group of unregistered users'
        )
        
        chats_group = service.create_role_group(
            name=RoleGroupEnum.CHATS,
            title_ru='Чаты',
            description_ru='Группа ролей для чатов в Телеграм',
            title_en='Chats',
            description_en='Group of Telegram chat roles'
        )
        
        # 2. Создание ролей
        print("\nСоздание ролей...")
        
        # Admin roles
        global_admin = service.create_role(
            name=RoleEnum.GLOBAL_ADMIN,
            title_ru='Глобальный администратор',
            description_ru='Глобальный администратор с полными правами',
            title_en='Global Administrator',
            description_en='Global administrator with full rights',
            group=admin_group
        )
        
        content_admin = service.create_role(
            name=RoleEnum.CONTENT_ADMIN,
            title_ru='Контент администратор',
            description_ru='Администратор контента',
            title_en='Content Administrator',
            description_en='Content administrator',
            group=admin_group
        )
        
        # User roles
        owner_role = service.create_role(
            name=RoleEnum.OWNER,
            title_ru='Владелец компании',
            description_ru='Владелец компании с расширенными правами',
            title_en='Company Owner',
            description_en='Company owner with extended rights',
            group=users_group
        )
        
        user_role = service.create_role(
            name=RoleEnum.USER,
            title_ru='Пользователь',
            description_ru='Обычный пользователь с базовыми правами',
            title_en='User',
            description_en='Regular user with basic rights',
            group=users_group
        )
        
        # Guest role
        guest_role = service.create_role(
            name=RoleEnum.GUEST,
            title_ru='Гость',
            description_ru='Незарегистрированный пользователь',
            title_en='Guest',
            description_en='Unregistered user',
            group=guests_group
        )
        
        # Chat role
        chat_role = service.create_role(
            name=RoleEnum.CHAT,
            title_ru='Чат',
            description_ru='Чат в Telegram',
            title_en='Chat',
            description_en='Telegram chat',
            group=chats_group
        )
        
        print("\n" + "="*50)
        print("Инициализация ролей завершена успешно!")
        print("="*50)
        
    except Exception as e:
        session.rollback()
        print("\n" + "="*50)
        print(f"Ошибка при инициализации ролей: {e}")
        print("="*50)
        raise
    finally:
        session.close()

if __name__ == "__main__":
    init_roles()