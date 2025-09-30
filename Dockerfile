FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Omsk

# Устанавливаем необходимые системные зависимости
RUN apt-get update && \
    apt-get install -y \
        wget \
        ca-certificates \
        xz-utils \
        fonts-liberation \
        fonts-noto-core \
        fonts-dejavu \
        fonts-dejavu-core \
        fonts-dejavu-extra \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем uv
RUN pip install uv

# Устанавливаем конкретную версию Typst (v0.13.1)
RUN wget https://github.com/typst/typst/releases/download/v0.13.1/typst-x86_64-unknown-linux-musl.tar.xz && \
    tar -xJf typst-x86_64-unknown-linux-musl.tar.xz && \
    mv typst-x86_64-unknown-linux-musl/typst /usr/local/bin/ && \
    rm -rf typst-x86_64-unknown-linux-musl.tar.xz typst-x86_64-unknown-linux-musl

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv export --no-dev > requirements.txt && \
    uv pip install --system -r requirements.txt

COPY . .

CMD ["python", "main.py"]


# create image:
    # docker build -t otbot .

# run container:
    # для обычного запуска
        # docker run -d -v "$(pwd)/otbot.db:/app/otbot.db" -v "$(pwd)/logs:/app/logs" --name otbot-ins otbot
    # для просмотра папок отчётов:
        # docker run -d -v "$(pwd)/otbot.db:/app/otbot.db" -v "$(pwd)/logs:/app/logs" -v "$(pwd)/typst:/app/typst" -v "$(pwd)/violations:/app/violations" --name otbot-ins otbot

# other commands:
    # docker ps -a  # Увидеть все контейнеры
    # docker logs otbot  # Посмотреть логи вашего бота
    # docker stop otbot # Остановить контейнер
    # docker rm otbot # Удалить контейнер

