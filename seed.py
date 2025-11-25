#!/usr/bin/env python3
"""
Скрипт заполнения базы данных для системы аутентификации.

Этот скрипт создает начальные данные, включая:
- Роль администратора со всеми разрешениями
- Роль пользователя по умолчанию с разрешениями на чтение
- Разрешения для документов, проектов, отчетов (read, create, update, delete)
- Начального администратора

Запустите этот скрипт после выполнения миграций базы данных:
    python seed.py
"""

import sys
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app.models import Base, User, Role, Permission
from app.utils.password import hash_password


def create_permissions(db: Session) -> dict[str, Permission]:
    """
    Создает все разрешения для системы.
    
    Возвращает словарь, сопоставляющий ключи разрешений с объектами Permission.
    """
    print("Создание разрешений...")
    
    resources = ["documents", "projects", "reports"]
    actions = ["read", "create", "update", "delete"]
    
    permissions = {}
    
    for resource in resources:
        for action in actions:
            permission_key = f"{resource}:{action}"
            
            # Проверяем, существует ли разрешение
            existing = db.query(Permission).filter_by(
                resource=resource,
                action=action
            ).first()
            
            if existing:
                print(f"  ✓ Разрешение '{permission_key}' уже существует")
                permissions[permission_key] = existing
            else:
                permission = Permission(
                    resource=resource,
                    action=action,
                    description=f"Permission to {action} {resource}"
                )
                db.add(permission)
                permissions[permission_key] = permission
                print(f"  + Создано разрешение '{permission_key}'")
    
    db.commit()
    print(f"✓ Создано {len(permissions)} разрешений\n")
    
    return permissions


def create_admin_role(db: Session, permissions: dict[str, Permission]) -> Role:
    """
    Создает роль администратора со всеми разрешениями.
    """
    print("Создание роли администратора...")
    
    # Проверяем, существует ли роль администратора
    existing_role = db.query(Role).filter_by(name="admin").first()
    
    if existing_role:
        print("  ✓ Роль администратора уже существует")
        # Обновляем разрешения, чтобы убедиться, что она имеет все разрешения
        existing_role.permissions = list(permissions.values())
        db.commit()
        print("  ✓ Обновлены разрешения роли администратора")
        return existing_role
    
    # Создаем роль администратора со всеми разрешениями
    admin_role = Role(
        name="admin",
        description="Роль администратора с полным доступом к системе"
    )
    admin_role.permissions = list(permissions.values())
    
    db.add(admin_role)
    db.commit()
    
    print(f"  + Создана роль администратора с {len(permissions)} разрешениями")
    print("✓ Роль администратора создана\n")
    
    return admin_role


def create_user_role(db: Session, permissions: dict[str, Permission]) -> Role:
    """
    Создает роль пользователя по умолчанию только с разрешениями на чтение.
    """
    print("Создание роли пользователя по умолчанию...")
    
    # Проверяем, существует ли роль пользователя
    existing_role = db.query(Role).filter_by(name="user").first()
    
    # Получаем только разрешения на чтение
    read_permissions = [
        perm for key, perm in permissions.items()
        if key.endswith(":read")
    ]
    
    if existing_role:
        print("  ✓ Роль пользователя уже существует")
        # Обновляем разрешения, чтобы убедиться, что она имеет разрешения на чтение
        existing_role.permissions = read_permissions
        db.commit()
        print("  ✓ Обновлены разрешения роли пользователя")
        return existing_role
    
    # Создаем роль пользователя с разрешениями на чтение
    user_role = Role(
        name="user",
        description="Роль пользователя по умолчанию с доступом только на чтение"
    )
    user_role.permissions = read_permissions
    
    db.add(user_role)
    db.commit()
    
    print(f"  + Создана роль пользователя с {len(read_permissions)} разрешениями на чтение")
    print("✓ Роль пользователя создана\n")
    
    return user_role


def create_admin_user(db: Session, admin_role: Role) -> User:
    """
    Создает начального пользователя-администратора.
    """
    print("Создание пользователя-администратора...")
    
    admin_email = "admin@example.com"
    
    # Проверяем, существует ли пользователь-администратор
    existing_user = db.query(User).filter_by(email=admin_email).first()
    
    if existing_user:
        print(f"  ✓ Пользователь-администратор '{admin_email}' уже существует")
        # Убеждаемся, что у пользователя-администратора есть роль администратора
        if admin_role not in existing_user.roles:
            existing_user.roles.append(admin_role)
            db.commit()
            print("  ✓ Назначена роль администратора существующему пользователю")
        return existing_user
    
    # Создаем пользователя-администратора
    admin_password = "admin123"  # Пароль по умолчанию - должен быть изменен после первого входа
    
    admin_user = User(
        first_name="System",
        last_name="Administrator",
        middle_name=None,
        email=admin_email,
        password_hash=hash_password(admin_password),
        is_active=True
    )
    admin_user.roles.append(admin_role)
    
    db.add(admin_user)
    db.commit()
    
    print(f"  + Создан пользователь-администратор:")
    print(f"    Email: {admin_email}")
    print(f"    Пароль: {admin_password}")
    print(f"    ⚠️  ВАЖНО: Измените этот пароль после первого входа!")
    print("✓ Пользователь-администратор создан\n")
    
    return admin_user


def seed_database():
    """
    Основная функция для заполнения базы данных начальными данными.
    """
    print("=" * 60)
    print("Система аутентификации - Скрипт заполнения БД")
    print("=" * 60)
    print()
    
    # Создаем сессию базы данных
    db = SessionLocal()
    
    try:
        # Создаем все разрешения
        permissions = create_permissions(db)
        
        # Создаем роль администратора со всеми разрешениями
        admin_role = create_admin_role(db, permissions)
        
        # Создаем роль пользователя по умолчанию с разрешениями на чтение
        user_role = create_user_role(db, permissions)
        
        # Создаем начального пользователя-администратора
        admin_user = create_admin_user(db, admin_role)
        
        print("=" * 60)
        print("✓ Заполнение базы данных успешно завершено!")
        print("=" * 60)
        print()
        print("Сводка:")
        print(f"  - Разрешения: {len(permissions)}")
        print(f"  - Роли: 2 (admin, user)")
        print(f"  - Пользователи: 1 (admin)")
        print()
        print("Теперь вы можете запустить приложение и войти с:")
        print(f"  Email: {admin_user.email}")
        print(f"  Пароль: admin123")
        print()
        
    except Exception as e:
        print(f"\n❌ Ошибка при заполнении базы данных: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
