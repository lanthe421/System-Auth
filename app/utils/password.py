"""Утилиты для хеширования паролей с использованием bcrypt."""

import bcrypt
from app.config import settings


def hash_password(password: str) -> str:
    """
    Хеширует пароль с использованием bcrypt.
    
    Args:
        password: Пароль в открытом виде для хеширования
        
    Returns:
        Хешированный пароль в виде строки
        
    Requirements: 1.4, 4.3
    """
    # Генерируем соль и хешируем пароль
    salt = bcrypt.gensalt(rounds=settings.BCRYPT_ROUNDS)
    password_bytes = password.encode('utf-8')
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Возвращаем как строку для хранения в базе данных
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Проверяет пароль против хеша.
    
    Args:
        password: Пароль в открытом виде для проверки
        password_hash: Хешированный пароль для сравнения
        
    Returns:
        True, если пароль соответствует хешу, иначе False
        
    Requirements: 1.4, 4.3
    """
    password_bytes = password.encode('utf-8')
    hash_bytes = password_hash.encode('utf-8')
    
    return bcrypt.checkpw(password_bytes, hash_bytes)
