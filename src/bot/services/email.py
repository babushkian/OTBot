import asyncio
from email.message import EmailMessage
from pathlib import Path
import aiosmtplib
import mimetypes
from bot.logger_config import log
from bot.config import settings

cred = settings.mail_credentials

async def send_email(to_email: str, subject :str, attachment: Path| None =None):
    msg = EmailMessage()
    msg["From"] = cred.email
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(subject)

    ctype, encoding = mimetypes.guess_file_type(attachment)
    if ctype is None or encoding is not None:
        ctype = 'application/octet-stream'
    maintype, subtype = ctype.split('/', 1)
    filename = attachment.name
    with attachment.open(mode="rb") as fp:
        msg.add_attachment(fp.read(),
                           maintype=maintype,
                           subtype=subtype,
                           filename=filename)

    try:
        await aiosmtplib.send(
            msg,
            hostname=cred.hostname,
            port=465,
            use_tls=True,
            username=cred.email,
            password=cred.password,
        )
        log.success("отправлено письмо """)
    except aiosmtplib.SMTPException as e:
        log.error("Ошибка при отправке письма.")
        log.exception(e)

async def send_email_parallel(recipients: list[str], subject: str, attachment: Path):
    tasks = [send_email(recipient, subject, attachment) for recipient in recipients]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Обработка результатов
    for result in results:
        if isinstance(result, tuple):
            recipient, success, message = result
            status = "✅" if success else "❌"
            print(f"{status} {recipient}: {message}")
        else:
            print(f"❌ Ошибка: {result}")