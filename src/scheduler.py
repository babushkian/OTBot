import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date

from bot.config import settings
from bot.services.email import  send_email_parallel
from bot.services.reports import make_daily_report, make_monthly_report, make_active_orders_report


async def send_daily_report():
    date_string = date.today().strftime("%Y.%m.%d")
    attachment = await make_daily_report()
    await send_email_parallel(settings.MAILING_LIST, f"ежедневный отчет {date_string}", attachment)


async def send_monthly_report():
    date_string = date.today().strftime("%Y.%m.%d")
    attachment = await make_monthly_report()
    await send_email_parallel(settings.MAILING_LIST, f"ежемесячный отчет {date_string}", attachment)

async def send_active_orders_report():
    date_string = date.today().strftime("%Y.%m.%d")
    attachment = await make_active_orders_report()
    await send_email_parallel(settings.MAILING_LIST, f"активные предписания {date_string}", attachment)


def create_scheduler() -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_report,
        CronTrigger(minute="*/3"),
        # CronTrigger(day="*", hour="17"),
        id="Ежедневный отчет",
    )
    scheduler.add_job(
        send_monthly_report,
        CronTrigger(minute="*/7"),
        # CronTrigger(day="last", hour="16", minute="2"),
        id = "Ежемесячный отчет",

    )
    scheduler.add_job(
        send_active_orders_report,
        CronTrigger(minute="*/5"),
        # CronTrigger(day_of_week="wed", hour="16"),
        id = "активные предписания",
    )
    return scheduler

async def main():
    scheduler = create_scheduler()
    scheduler.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())