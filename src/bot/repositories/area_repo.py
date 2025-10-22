"""Репозитории места нарушения."""
from typing import Any

from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import AreaModel
from bot.logger_config import log


class AreaRepository:
    """Репозиторий места нарушения."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория места нарушения."""
        self.session = session

    async def get_area_by_id(self, area_id: int) -> AreaModel | None:
        """Получение места нарушения по id."""
        try:
            result = await self.session.execute(select(AreaModel).where(AreaModel.id == area_id))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting area with id {area_id}", area_id=area_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting area with idd {area_id}", area_id=area_id)
            log.exception(e)
            return None
        else:
            log.success("Area with id {area_id} found successfully", area_id=area_id)
            return result.scalars().first()

    async def get_all_areas(self) -> tuple[AreaModel, ...] | None:
        """Получение всех мест нарушения."""
        try:
            result = await self.session.execute(select(AreaModel))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting areas")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting areas")
            log.exception(e)
            return None
        else:
            areas = tuple(result.scalars().all())
            log.success("{col} Areas found successfully", col=len(areas))
            return areas

    async def add_area(self, area: AreaModel) -> AreaModel | None:
        """Добавление места нарушения."""
        try:
            self.session.add(area)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError adding area {area}", area=area.name)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error adding area {area}", area=area.name)
            log.exception(e)
            return None
        else:
            log.success("Area {area} added successfully", area=area.name)
            return area

    async def update_area(self, area_id: int, update_data: dict[str, Any]) -> AreaModel | None:
        """Обновление места нарушения по id."""
        stmt = (
            update(AreaModel)
            .where(AreaModel.id == area_id)
            .values(**update_data)
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError updating area with id {area}", area=area_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error updating area with id {area}", area=area_id)
            log.exception(e)
            return None
        else:
            log.success("Area data with id {area} updated successfully: {update_data}",
                        area=area_id, update_data=update_data)

    async def delete_area_by_id(self, area_id: int) -> None:
        """Удаление данных места нарушения по area_id."""
        stmt = (
            delete(AreaModel)
            .where(AreaModel.id == area_id)
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError deleting area with id {area}", area=area_id)
            log.exception(e)
            return
        except Exception as e:
            log.error("Error deleting area with id {area}", area=area_id)
            log.exception(e)
            return
        else:
            log.success("Area with id {area} deleted successfully", area=area_id)
