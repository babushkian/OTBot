"""Репозитории зарегистрированного нарушения."""
from typing import Any
from datetime import datetime

from sqlalchemy import delete, select, update, between
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from bot.enums import ViolationStatus
from bot.db.models import AreaModel, ViolationModel
from logger_config import log


class ViolationRepository:
    """Репозиторий нарушения."""

    def __init__(self, session: AsyncSession) -> None:
        """Инициализация репозитория нарушения."""
        self.session = session

    async def get_violation_by_id(self, violation_id: int) -> dict[str, Any] | None:
        """Получение нарушения по id."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                                .where(ViolationModel.id == violation_id)
                                                .options(joinedload(ViolationModel.area)
                                                         .options(joinedload(AreaModel.responsible_user)),
                                                         joinedload(ViolationModel.detector),
                                                         ),
                                                )
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting violation with id {violation_id}", violation_id=violation_id)
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting violation with id {violation_id}", violation_id=violation_id)
            log.exception(e)
            return None
        else:
            log.success("Violation with id {violation_id} found successfully", violation_id=violation_id)

            violation = result.scalars().first()
            if not violation:
                return None

            responsible_user = violation.area.responsible_user.to_dict() if violation.area.responsible_user else None
            return (violation.to_dict() |
                    {"area": violation.area.to_dict() | {"responsible_user": responsible_user}}
                    | {"detector": violation.detector.to_dict()})

    async def get_all_violations(self) -> [dict, ...]:
        """Получение всех мест нарушения."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                                .options(joinedload(ViolationModel.area)
                                                         .options(joinedload(AreaModel.responsible_user)),
                                                         joinedload(ViolationModel.detector),
                                                         ),
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
            violations = tuple(result.scalars().all())
            log.success("{col} violations found successfully", col=len(violations))

            return tuple([
                (violation.to_dict() |
                 {
                     "area": violation.area.to_dict() | {
                         "responsible_user": violation.area.responsible_user.to_dict()
                         if violation.area.responsible_user else None},
                 }
                 | {"detector": violation.detector.to_dict()}) for violation in violations
            ])

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
            return
        except Exception as e:
            log.error("Error deleting violation with id {violation}", violation=violation_id)
            log.exception(e)
            return
        else:
            log.success("Violation with id {violation} deleted successfully", violation=violation_id)

    async def get_not_reviewed_violations(self) -> tuple[dict, ...] | None:
        """Получение всех непроверенных нарушений."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                                .options(joinedload(ViolationModel.area)
                                                         .options(joinedload(AreaModel.responsible_user)),
                                                         joinedload(ViolationModel.detector),
                                                         )
                                                .where(ViolationModel.status == ViolationStatus.REVIEW))
        except SQLAlchemyError as e:
            await self.session.rollback()
            log.error("SQLAlchemyError getting not reviewed violations")
            log.exception(e)
            return None
        except Exception as e:
            log.error("Error getting not reviewed violations")
            log.exception(e)
            return None
        else:
            log.success("Not reviewed violations found successfully")
            violations = tuple(result.scalars().all())
            return tuple([
                (violation.to_dict() |
                 {
                     "area": violation.area.to_dict() | {
                         "responsible_user": violation.area.responsible_user.to_dict()
                         if violation.area.responsible_user else None},
                 }
                 | {"detector": violation.detector.to_dict()}) for violation in violations
            ])

    async def get_active_violations(self) -> tuple[dict, ...] | None:
        """Получение всех активных нарушений."""
        try:
            result = await self.session.execute(select(ViolationModel)
                                                .options(joinedload(ViolationModel.area)
                                                         .options(joinedload(AreaModel.responsible_user)),
                                                         joinedload(ViolationModel.detector),
                                                         )
                                                .where(ViolationModel.status == ViolationStatus.ACTIVE))
        except SQLAlchemyError as e:
            await self.session.rollback()
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
            return tuple([
                (violation.to_dict() |
                 {
                     "area": violation.area.to_dict() | {
                         "responsible_user": violation.area.responsible_user.to_dict()
                         if violation.area.responsible_user else None},
                 }
                 | {"detector": violation.detector.to_dict()}) for violation in violations
            ])

    async def get_all_violations_by_date(self,
                                         start_date: datetime,
                                         end_date: datetime) -> [dict, ...]:
        """Получение нарешений в периоде дет."""
        try:
            result = await self.session.execute(select(ViolationModel).order_by(ViolationModel.id)
                                                .options(joinedload(ViolationModel.area)
                                                         .options(joinedload(AreaModel.responsible_user)),
                                                         joinedload(ViolationModel.detector),
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
            violations = tuple(result.scalars().all())
            log.success("{col} violations found successfully", col=len(violations))

            return tuple([
                (violation.to_dict() |
                 {
                     "area": violation.area.to_dict() | {
                         "responsible_user": violation.area.responsible_user.to_dict()
                         if violation.area.responsible_user_id else None},
                 }
                 | {"detector": violation.detector.to_dict()}) for violation in violations
            ])

    async def get_active_violations_id_description(self) -> tuple[dict, ...] | None:
        """Получение всех активных нарушений."""
        try:
            result = await self.session.execute(select(ViolationModel.id, ViolationModel.description)
                                                .where(ViolationModel.status == ViolationStatus.ACTIVE))
        except SQLAlchemyError as e:
            await self.session.rollback()
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
            return tuple([violation.to_dict() for violation in violations])
