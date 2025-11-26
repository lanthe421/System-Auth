-- ============================================================
-- SQL Примеры для Auth System
-- ============================================================
-- Используйте эти запросы в DBeaver или psql для работы с БД
-- ============================================================

-- ============================================================
-- ПРОСМОТР ДАННЫХ
-- ============================================================

-- Все пользователи
SELECT * FROM users;

-- Все роли
SELECT * FROM roles;

-- Все разрешения
SELECT * FROM permissions;

-- Активные сессии
SELECT * FROM sessions WHERE is_valid = true;

-- ============================================================
-- ПОЛЬЗОВАТЕЛИ С РОЛЯМИ
-- ============================================================

-- Пользователи и их роли
SELECT 
    u.id,
    u.email,
    u.first_name,
    u.last_name,
    u.is_active,
    r.name as role_name,
    ur.assigned_at
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON r.id = ur.role_id
ORDER BY u.email;

-- Только активные пользователи с ролями
SELECT 
    u.email,
    u.first_name || ' ' || u.last_name as full_name,
    STRING_AGG(r.name, ', ') as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON r.id = ur.role_id
WHERE u.is_active = true
GROUP BY u.id, u.email, u.first_name, u.last_name
ORDER BY u.email;

-- ============================================================
-- РОЛИ И РАЗРЕШЕНИЯ
-- ============================================================

-- Роли с их разрешениями
SELECT 
    r.name as role_name,
    r.description,
    p.resource,
    p.action,
    p.description as permission_description
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON p.id = rp.permission_id
ORDER BY r.name, p.resource, p.action;

-- Количество разрешений у каждой роли
SELECT 
    r.name as role_name,
    COUNT(rp.permission_id) as permissions_count
FROM roles r
LEFT JOIN role_permissions rp ON r.id = rp.role_id
GROUP BY r.id, r.name
ORDER BY permissions_count DESC;

-- Разрешения, сгруппированные по ресурсам
SELECT 
    resource,
    STRING_AGG(action, ', ' ORDER BY action) as actions
FROM permissions
GROUP BY resource
ORDER BY resource;

-- ============================================================
-- ПРЯМЫЕ РАЗРЕШЕНИЯ ПОЛЬЗОВАТЕЛЕЙ
-- ============================================================

-- Пользователи с прямыми разрешениями
SELECT 
    u.email,
    p.resource,
    p.action,
    up.granted_at
FROM users u
JOIN user_permissions up ON u.id = up.user_id
JOIN permissions p ON p.id = up.permission_id
ORDER BY u.email, p.resource, p.action;

-- ============================================================
-- ВСЕ РАЗРЕШЕНИЯ ПОЛЬЗОВАТЕЛЯ (роли + прямые)
-- ============================================================

-- Все разрешения конкретного пользователя
WITH user_email AS (
    SELECT 'admin@example.com' as email  -- Замените на нужный email
)
SELECT DISTINCT
    p.resource,
    p.action,
    CASE 
        WHEN rp.role_id IS NOT NULL THEN 'Через роль: ' || r.name
        ELSE 'Прямое разрешение'
    END as source
FROM users u
CROSS JOIN user_email ue
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON r.id = ur.role_id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p ON p.id = rp.permission_id
WHERE u.email = ue.email

UNION

SELECT DISTINCT
    p.resource,
    p.action,
    'Прямое разрешение' as source
FROM users u
CROSS JOIN user_email ue
JOIN user_permissions up ON u.id = up.user_id
JOIN permissions p ON p.id = up.permission_id
WHERE u.email = ue.email

ORDER BY resource, action;

-- ============================================================
-- СЕССИИ И АУТЕНТИФИКАЦИЯ
-- ============================================================

-- Активные сессии с информацией о пользователях
SELECT 
    u.email,
    u.first_name,
    u.last_name,
    s.created_at as login_time,
    s.expires_at,
    EXTRACT(EPOCH FROM (s.expires_at - NOW())) / 60 as minutes_until_expiry
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.is_valid = true 
  AND s.expires_at > NOW()
ORDER BY s.created_at DESC;

-- История входов (все сессии)
SELECT 
    u.email,
    s.created_at as login_time,
    s.expires_at,
    s.is_valid,
    CASE 
        WHEN s.expires_at < NOW() THEN 'Истекла'
        WHEN s.is_valid = false THEN 'Инвалидирована'
        ELSE 'Активна'
    END as status
FROM sessions s
JOIN users u ON s.user_id = u.id
ORDER BY s.created_at DESC
LIMIT 50;

-- Количество сессий по пользователям
SELECT 
    u.email,
    COUNT(*) as total_sessions,
    COUNT(CASE WHEN s.is_valid = true AND s.expires_at > NOW() THEN 1 END) as active_sessions
FROM users u
LEFT JOIN sessions s ON u.id = s.user_id
GROUP BY u.id, u.email
ORDER BY total_sessions DESC;

-- ============================================================
-- СТАТИСТИКА
-- ============================================================

-- Общая статистика системы
SELECT 
    (SELECT COUNT(*) FROM users) as total_users,
    (SELECT COUNT(*) FROM users WHERE is_active = true) as active_users,
    (SELECT COUNT(*) FROM roles) as total_roles,
    (SELECT COUNT(*) FROM permissions) as total_permissions,
    (SELECT COUNT(*) FROM sessions WHERE is_valid = true AND expires_at > NOW()) as active_sessions;

-- Пользователи по ролям
SELECT 
    r.name as role_name,
    COUNT(ur.user_id) as user_count
FROM roles r
LEFT JOIN user_roles ur ON r.id = ur.role_id
GROUP BY r.id, r.name
ORDER BY user_count DESC;

-- Последние зарегистрированные пользователи
SELECT 
    email,
    first_name,
    last_name,
    created_at,
    is_active
FROM users
ORDER BY created_at DESC
LIMIT 10;

-- ============================================================
-- ПОИСК И ФИЛЬТРАЦИЯ
-- ============================================================

-- Поиск пользователя по email (частичное совпадение)
SELECT * FROM users 
WHERE email ILIKE '%example%'
ORDER BY email;

-- Поиск пользователя по имени
SELECT * FROM users 
WHERE first_name ILIKE '%john%' 
   OR last_name ILIKE '%john%'
ORDER BY last_name, first_name;

-- Пользователи с определенной ролью
SELECT 
    u.email,
    u.first_name,
    u.last_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON r.id = ur.role_id
WHERE r.name = 'admin'  -- Замените на нужную роль
ORDER BY u.email;

-- Пользователи с определенным разрешением
SELECT DISTINCT
    u.email,
    u.first_name,
    u.last_name
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON r.id = ur.role_id
LEFT JOIN role_permissions rp ON r.id = rp.role_id
LEFT JOIN permissions p1 ON p1.id = rp.permission_id
LEFT JOIN user_permissions up ON u.id = up.user_id
LEFT JOIN permissions p2 ON p2.id = up.permission_id
WHERE (p1.resource = 'documents' AND p1.action = 'create')
   OR (p2.resource = 'documents' AND p2.action = 'create')
ORDER BY u.email;

-- ============================================================
-- АУДИТ И БЕЗОПАСНОСТЬ
-- ============================================================

-- Неактивные пользователи
SELECT 
    email,
    first_name,
    last_name,
    created_at,
    updated_at
FROM users
WHERE is_active = false
ORDER BY updated_at DESC;

-- Пользователи без ролей
SELECT 
    u.email,
    u.first_name,
    u.last_name,
    u.created_at
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
WHERE ur.role_id IS NULL
  AND u.is_active = true
ORDER BY u.created_at DESC;

-- Истекшие сессии за последние 24 часа
SELECT 
    u.email,
    s.created_at,
    s.expires_at
FROM sessions s
JOIN users u ON s.user_id = u.id
WHERE s.expires_at BETWEEN NOW() - INTERVAL '24 hours' AND NOW()
  AND s.expires_at < NOW()
ORDER BY s.expires_at DESC;

-- ============================================================
-- АДМИНИСТРАТИВНЫЕ ОПЕРАЦИИ
-- ============================================================

-- Назначить роль пользователю (пример)
-- INSERT INTO user_roles (user_id, role_id, assigned_at)
-- VALUES (
--     (SELECT id FROM users WHERE email = 'user@example.com'),
--     (SELECT id FROM roles WHERE name = 'admin'),
--     NOW()
-- );

-- Отозвать роль у пользователя (пример)
-- DELETE FROM user_roles
-- WHERE user_id = (SELECT id FROM users WHERE email = 'user@example.com')
--   AND role_id = (SELECT id FROM roles WHERE name = 'admin');

-- Предоставить прямое разрешение (пример)
-- INSERT INTO user_permissions (user_id, permission_id, granted_at)
-- VALUES (
--     (SELECT id FROM users WHERE email = 'user@example.com'),
--     (SELECT id FROM permissions WHERE resource = 'documents' AND action = 'create'),
--     NOW()
-- );

-- Деактивировать пользователя (пример)
-- UPDATE users 
-- SET is_active = false, updated_at = NOW()
-- WHERE email = 'user@example.com';

-- Инвалидировать все сессии пользователя (пример)
-- UPDATE sessions
-- SET is_valid = false
-- WHERE user_id = (SELECT id FROM users WHERE email = 'user@example.com');

-- ============================================================
-- ОЧИСТКА И ОБСЛУЖИВАНИЕ
-- ============================================================

-- Удалить истекшие сессии старше 30 дней
-- DELETE FROM sessions
-- WHERE expires_at < NOW() - INTERVAL '30 days';

-- Удалить инвалидированные сессии старше 7 дней
-- DELETE FROM sessions
-- WHERE is_valid = false 
--   AND created_at < NOW() - INTERVAL '7 days';

-- ============================================================
-- СТРУКТУРА БАЗЫ ДАННЫХ
-- ============================================================

-- Список всех таблиц
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Структура таблицы users
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'users'
ORDER BY ordinal_position;

-- Все индексы
SELECT 
    tablename,
    indexname,
    indexdef
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;

-- Внешние ключи
SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
ORDER BY tc.table_name, kcu.column_name;

-- ============================================================
-- РЕЗЕРВНОЕ КОПИРОВАНИЕ (команды для выполнения в терминале)
-- ============================================================

-- Создать дамп базы данных:
-- pg_dump -h localhost -p 8888 -U postgres -d postgres > backup.sql

-- Восстановить из дампа:
-- psql -h localhost -p 8888 -U postgres -d postgres < backup.sql

-- Создать дамп только данных (без структуры):
-- pg_dump -h localhost -p 8888 -U postgres -d postgres --data-only > data_backup.sql

-- Создать дамп только структуры (без данных):
-- pg_dump -h localhost -p 8888 -U postgres -d postgres --schema-only > schema_backup.sql
