from email.message import EmailMessage
from pathlib import Path
import aiosmtplib
import mimetypes
from bot.logger_config import log



async def send_email(to_email: str, subject :str, attachment: Path| None =None):
    msg = EmailMessage()
    msg["From"] = "terminal@omzit.ru"
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
            hostname="smtp.timeweb.ru",
            port=465,
            use_tls=True,
            username="terminal@omzit.ru",
            password="pgw9k7I90u",
        )
    except aiosmtplib.SMTPException as e:
        log.error("Ошибка при отправке письма.")
        log.exception(e)