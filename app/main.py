from fastapi import FastAPI
from app.config import settings
from app.api.auth import router as auth_router
from app.api.users import router as users_router
from app.api.admin import router as admin_router
from app.api.resources import router as resources_router
from app.error_handlers import register_exception_handlers

app = FastAPI(
    title=settings.APP_NAME,
    debug=settings.DEBUG
)

# Регистрируем глобальные обработчики исключений
register_exception_handlers(app)

# Подключаем роутеры
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(resources_router)


@app.get("/")
async def root():
    """Эндпоинт проверки работоспособности."""
    return {"message": "Auth System API", "status": "running"}


@app.get("/health")
async def health():
    """Эндпоинт проверки работоспособности."""
    return {"status": "healthy"}
