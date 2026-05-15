FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/

ENV DOWNLOAD_DIR=/tmp/downloads
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

EXPOSE 10000

CMD ["python", "-m", "bot.main"]
