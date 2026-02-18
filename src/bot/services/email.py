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
        log.success("отправлено письмо {f} на адрес {e}", f=filename, e=to_email)
    # except aiosmtplib.SMTPException as e:
    except Exception as e:
        log.error("Ошибка при отправке письма {f} на адрес {e}.", f=filename, e=to_email)
        log.exception(e)
        raise

async def send_email_parallel(recipients: list[str], subject: str, attachment: Path, max_attempts: int = 4):
    recs = recipients.copy()

    attempt = 0
    timeout = 1
    while True:
        log.info("Попытка отправки на адреса {addr} № {attempt}", attempt = attempt, addr = recs)
        tasks = [send_email(recipient, subject, attachment) for recipient in recs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        log.info("результаты попытки № {attempt}: {r}", attempt=attempt, r=results)
        attempt += 1
        timeout *= 2
        new_recs = []
        for res, recipient in zip(results, recs):
            if isinstance(res, Exception):
                log.info("Замечена ошибка при отправке письма")
                new_recs.append(recipient)
        recs = new_recs
        if not recs or attempt >= max_attempts:
            break
        await asyncio.sleep(20 * timeout)
    log.info("Отправка {subj} завершена, оставшиеся ошибки {recs}", subj = subject, recs=recs )
