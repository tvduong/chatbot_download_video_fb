FROM python:3.12-slim-bookworm

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot/ bot/

ENV PYTHONUNBUFFERED=1
ENV RENDER=true

CMD ["python", "-m", "bot.main"]
