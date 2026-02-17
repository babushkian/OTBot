from datetime import datetime, timedelta
from bot.constants import tz
from bot.repositories.violation_repo import ViolationRepository
from bot.repositories.user_repo import UserRepository
from bot.handlers.reports_handlers.create_reports import create_typst_report
from bot.db.database import async_session_factory

async def make_daily_report(user_id: int = 2):
    start_date = datetime.now(tz=tz) - timedelta(days=1)
    end_date = datetime.now(tz=tz)
    async with async_session_factory() as session:
        violations = await ViolationRepository(session).get_all_violations_by_date(start_date, end_date)
        user = await UserRepository(session).get_user_by_id(user_id)
        return create_typst_report(user, violations)


async def make_monthly_report(user_id: int = 2):
    end_date = datetime.now(tz=tz)
    start_date = datetime.now(tz=tz).replace(day=1, hour=0, minute=0, second=0)
    async with async_session_factory() as session:
        violations = await ViolationRepository(session).get_all_violations_by_date(start_date, end_date)
        user = await UserRepository(session).get_user_by_id(user_id)
        return create_typst_report(user, violations)


async def make_active_orders_report(user_id: int = 2):
    async with async_session_factory() as session:
        violations = await ViolationRepository(session).get_active_violations()
        user = await UserRepository(session).get_user_by_id(user_id)
        return create_typst_report(user, violations)
