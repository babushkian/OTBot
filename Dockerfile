FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Omsk

# Устанавливаем необходимые системные зависимости
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        fontconfig \
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

COPY alembic.ini ./
COPY src ./

CMD ["python", "main.py"]


