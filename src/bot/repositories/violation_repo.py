"""Репозитории зарегистрированного нарушения."""
from typing import Any, Sequence
from datetime import datetime

from sqlalchemy import delete, select, update, between, func, extract
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import ViolationStatus
from bot.db.models import AreaModel, ViolationModel
from bot.logger_config import log


class ViolationRepository:
    """Репозиторий нарушения."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория нарушения."""
        self.session = session

    async def get_violation_by_id(self, violation_id: int) -> ViolationModel | None:
        """Получение нарушения по id."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                                .where(ViolationModel.id == violation_id)
                                                .options(joinedload(ViolationModel.area)
                                                         .options(joinedload(AreaModel.responsible_user)),
                                                         joinedload(ViolationModel.detector),
                                                         selectinload(ViolationModel.files)
                                                         ),
                                                )
        except SQLAlchemyError as e:
            log.error("SQLAlchemyError getting violation with id {violation_id}", violation_id=violation_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting violation with id {violation_id}", violation_id=violation_id)
            log.exception(e)
            return None
        else:
            log.success("Violation with id {violation_id} found successfully", violation_id=violation_id)
            violation = result.unique().scalar_one_or_none()

            if not violation:
                return None
            return violation


    async def get_violation_by_number(self, violation_number: int) -> ViolationModel | None:
        """Получение нарушения по номеру.
            Так как номера уникальны только в пределах одного года, то выбираются все нарушения с указанным номером
            и возвращается последняя по дате запись.
        """
        try:
            result = await self.session.execute(
                select(ViolationModel)
                .where(ViolationModel.number == violation_number)
                .order_by(ViolationModel.created_at.desc()) # сортируется по дате по убыванию, чтобы взять последний
                .options(
                    joinedload(ViolationModel.area)
                    .options(joinedload(AreaModel.responsible_user)),
                    joinedload(ViolationModel.detector),
                    selectinload(ViolationModel.files)
                )
            )
        except SQLAlchemyError as e:
            log.error("SQLAlchemyError getting violation with number {violation_number}", violation_number=violation_number)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting violation with number {violation_number}", violation_number=violation_number)
            log.exception(e)
            return None
        else:
            log.success("Violation with number {violation_number} found successfully", violation_number=violation_number)
            violation = result.scalars().first()
            log.info(violation)
            log.info(violation.id)
            log.info(violation.number)
            if not violation:
                return None
            return violation


    async def get_all_violations(self) -> Sequence[ViolationModel] | None:
        """Получение всех мест нарушения."""
        try:
            result = await self.session.execute(select(ViolationModel)
                        .options(joinedload(ViolationModel.area).joinedload(AreaModel.responsible_user),
                                 joinedload(ViolationModel.detector),
                                 )
                        )
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting violations")
            log.exception(e)
            return tuple()
        except Exception as e:
            log.error("Error getting violations")
            log.exception(e)
            return tuple()
        else:
            violations = result.scalars().all()
            log.success("{col} violations found successfully", col=len(violations))
            return violations


    async def get_max_number(self):
        """Возвращает последний номер нарушения в этом году."""
        current_year = datetime.now().year
        stmt = (select(func.max(ViolationModel.number))
                    .where(
                        extract("year", ViolationModel.created_at) ==current_year
                    )
                )
        try:
            result  = (await self.session.execute(stmt)).scalar()
            log.success("результат запроса номера {number}", number= result)
        except Exception as e:
            log.error("Ошибка при получении номера последнего поручения.")
            log.exception(e)
            raise
        return result or 0


    async def add_violation(self, violation: ViolationModel) -> ViolationModel | None:
        """Добавление нарушения."""
        try:
            self.session.add(violation)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError adding violation {violation}", violation=violation.description)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error adding violation {violation}", violation=violation.description)
            log.exception(e)
            return None
        else:
            log.success("Violation {violation} added successfully", violation=violation.description)
            return violation


    async def update_violation(self, violation_id: int, update_data: dict[str, Any]) -> bool:
        """Обновление места нарушения по id."""
        stmt = (
            update(ViolationModel)
            .where(ViolationModel.id == violation_id)
            .values(**update_data)
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError updating violation with id {violation}", violation=violation_id)
            log.exception(e)
            return False
        except Exception as e:
            log.error("Error updating area violation id {violation}", violation=violation_id)
            log.exception(e)
            return False
        else:
            log.success("Violation data with id {violation} updated successfully: {update_data}",
                        violation=violation_id, update_data=update_data)
            return True


    async def delete_violation_by_id(self, violation_id: int) -> None:
        """Удаление данных нарушения по violation_id."""
        stmt = (
            delete(ViolationModel)
            .where(ViolationModel.id == violation_id)
        )
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError deleting violation with id {violation}", violation=violation_id)
            log.exception(e)
        except Exception as e:
            log.error("Error deleting violation with id {violation}", violation=violation_id)
            log.exception(e)
        else:
            log.success("Violation with id {violation} deleted successfully", violation=violation_id)
        return None


    async def get_not_reviewed_violations(self) -> Sequence[ViolationModel] | None:
        """Получение всех непроверенных нарушений."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                .options(joinedload(ViolationModel.area).joinedload(AreaModel.responsible_user),
                                         joinedload(ViolationModel.detector),
                                         selectinload(ViolationModel.files),
                                         )
                                .where(ViolationModel.status == ViolationStatus.REVIEW))
        except SQLAlchemyError as e:
            log.error("SQLAlchemyError getting not reviewed violations")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting not reviewed violations")
            log.exception(e)
            return None
        else:
            log.success("Not reviewed violations found successfully")
            return result.unique().scalars().all()


    async def get_active_violations(self) -> Sequence[ViolationModel]| None:
        """Получение всех активных нарушений."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                                .options(joinedload(ViolationModel.area)
                                                         .joinedload(AreaModel.responsible_user),
                                                         joinedload(ViolationModel.detector),
                                                         selectinload(ViolationModel.files),
                                                         )
                                                .where(ViolationModel.status == ViolationStatus.ACTIVE))
        except SQLAlchemyError as e:
            log.error("SQLAlchemyError getting active violations")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting active violations")
            log.exception(e)
            return None
        else:
            log.success("Active violations found successfully")
            violations = result.unique().scalars().all()
            return violations


    async def get_all_violations_by_date(self,
                                         start_date: datetime,
                                         end_date: datetime) -> Sequence[ViolationModel]| None:
        """Получение нарешений в периоде дет."""
        try:
            result = await self.session.execute(select(ViolationModel).order_by(ViolationModel.id)
                                            .options(joinedload(ViolationModel.area)
                                                     .joinedload(AreaModel.responsible_user),
                                                     joinedload(ViolationModel.detector),
                                                     selectinload(ViolationModel.files),
                                                     )
                                            .where(between(ViolationModel.created_at, start_date, end_date)),
                                            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting violations")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting violations")
            log.exception(e)
            return None
        else:
            violations = result.unique().scalars().all()
            log.success("{col} violations found successfully", col=len(violations))

            return violations


    async def get_all_active_violations_by_date(self,
                                                start_date: datetime,
                                                end_date: datetime) -> Sequence[ViolationModel]| None:
        """Получение нарешений в периоде дет."""
        try:
            result = await self.session.execute(select(ViolationModel).order_by(ViolationModel.id)
                                                .options(joinedload(ViolationModel.area)
                                                         .joinedload(AreaModel.responsible_user),
                                                         joinedload(ViolationModel.detector),
                                                         selectinload(ViolationModel.files),
                                                         )
                                                .where(between(ViolationModel.created_at, start_date, end_date))
                                                .where(ViolationModel.status == ViolationStatus.ACTIVE),
                                                )
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting violations")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting violations")
            log.exception(e)
            return None
        else:
            violations = result.unique().scalars().all()
            log.success("{col} violations found successfully", col=len(violations))

            return violations


    async def get_active_violations_id_description(self) -> Sequence[ViolationModel]| None | None:
        """Получение всех активных нарушений."""
        try:
            result = await self.session.execute(select(ViolationModel.id, ViolationModel.description)
                                                .where(ViolationModel.status == ViolationStatus.ACTIVE))
        except SQLAlchemyError as e:
            log.error("SQLAlchemyError getting active violations")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting active violations")
            log.exception(e)
            return None
        else:
            log.success("Active violations found successfully")
            violations = tuple(result.scalars().all())
            log.debug(violations)
            return tuple([violation.to_dict() for violation in violations])
