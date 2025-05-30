FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1

RUN pip install uv

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv export --no-dev  > requirements.txt && \
    uv pip install --system -r requirements.txt

COPY . .

CMD ["python", "main.py"]


# create image:
    # docker build -t otbot .

# run container:
    # docker run -d -v "$(pwd)/bot.db:/app/bot.db" -v "$(pwd)/violations:/app/violations" -v "$(pwd)/logs:/app/logs" --name otbot-ins otbot

# other commands:
    # docker ps -a  # Увидеть все контейнеры
    # docker logs otbot  # Посмотреть логи вашего бота
    # docker stop otbot # Остановить контейнер
    # docker rm otbot # Удалить контейнер

