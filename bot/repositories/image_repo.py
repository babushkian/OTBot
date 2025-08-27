from sqlalchemy.ext.asyncio import AsyncSession
from bot.db.models import FileModel
class ImageRepository:
    """Репозиторий нарушения."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория нарушения."""
        self.session = session

    async def get(self, hash: str) -> FileModel | None:
        """Получение изображения по хэш-сумме"""


    async def add(self, file: FileModel) -> None:
        """Добавление изображения в базу"""
        self.session.add(file)
        self.session.commit()
