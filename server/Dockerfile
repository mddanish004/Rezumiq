FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl xz-utils ca-certificates \
    && curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.17.0/tectonic-0.17.0-x86_64-unknown-linux-musl.tar.gz" \
        | tar -xz -C /usr/local/bin tectonic \
    && tectonic --version \
    && apt-get purge -y --auto-remove curl xz-utils \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN DJANGO_SECRET_KEY=build-only-dummy DATABASE_URL=postgres://build@localhost/build COMPILE_TIMEOUT_MS=600000 \
    python manage.py warm_templates

RUN DJANGO_SECRET_KEY=build-only-dummy DATABASE_URL=postgres://build@localhost/build \
    python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn rezumiq.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --threads ${GUNICORN_THREADS:-2} --timeout ${GUNICORN_TIMEOUT:-120}"]
