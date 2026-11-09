FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt ./requirements.txt
RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -r requirements.txt
COPY app ./app
RUN useradd --create-home --uid 10001 app \
    && chown -R app:app /app
COPY docker-entrypoint.sh /usr/local/bin/photographer-entrypoint
RUN chmod 755 /usr/local/bin/photographer-entrypoint

EXPOSE 8000
ENTRYPOINT ["photographer-entrypoint"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
