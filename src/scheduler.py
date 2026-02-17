import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, date
from bot.constants import tz
from bot.services.email import send_email
from bot.services.reports import make_daily_report, make_monthly_report, make_active_orders_report



async def send_daily_report():
    date_string = date.today().strftime("%Y.%m.%d")
    attachment = await make_daily_report()
    await send_email("asup02@omzit.ru", f"ежедневный отчет {date_string}", attachment)


async def send_monthly_report():
    date_string = date.today().strftime("%Y.%m.%d")
    attachment = await make_monthly_report()
    await send_email("asup02@omzit.ru", f"ежемесячный отчет {date_string}", attachment)

async def send_active_orders_report():
    date_string = date.today().strftime("%Y.%m.%d")
    attachment = await make_active_orders_report()
    await send_email("asup02@omzit.ru", f"активные предписания {date_string}", attachment)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_report,
        # CronTrigger(minute="*")
        CronTrigger(day="*", hour="17")
    )
    scheduler.add_job(
        send_monthly_report,
        # CronTrigger(minute="*/5")
        CronTrigger(day="last", hour="16", minute="2")

    )
    scheduler.add_job(
        send_active_orders_report,
        # CronTrigger(minute="*/2")
        CronTrigger(day_of_week="wed", hour="16")
    )
    return scheduler

async def main():
    scheduler = create_scheduler()
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())