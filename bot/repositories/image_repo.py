from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from bot.db.models import FileModel
class ImageRepository:
    """Репозиторий нарушения."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория нарушения."""
        self.session = session

    async def get(self, hash: str) -> FileModel | None:
        """Получение изображения по хэш-сумме"""
        stmt = select(FileModel).where(FileModel.hash==hash)
        await self.session.execute(stmt).calar_one_or_none()
        return

    async def add(self, file: FileModel) -> None:
        """Добавление изображения в базу"""
        self.session.add(file)
        await self.session.commit()
