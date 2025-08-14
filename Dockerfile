# docker build -t selenium_chrome_full:latest .
FROM python:3.12.2 AS builder

WORKDIR /app

COPY . /app

COPY ./requirements.txt /app/requirements.txt
COPY ./app/*.py /app/

RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r /app/requirements.txt


FROM python:3.12.2-slim

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
COPY --from=builder /app/*.py /app/

RUN pip install --no-cache /wheels/*

ENTRYPOINT ["python", "scraper.py"]
