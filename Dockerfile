FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY requirements.txt .
RUN python -m pip wheel --only-binary=:all: --wheel-dir=/wheels -r requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-index --find-links=/wheels -r requirements.txt

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
RUN groupadd --gid 10001 halcyon \
    && useradd --uid 10001 --gid halcyon --create-home halcyon
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --chown=halcyon:halcyon config config
COPY --chown=halcyon:halcyon tickets tickets
COPY --chown=halcyon:halcyon manage.py docker-entrypoint.sh ./
RUN DJANGO_SECRET_KEY=build-only-static-collection-key python manage.py collectstatic --noinput
USER halcyon
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=8s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/', timeout=6)" || exit 1
ENTRYPOINT ["sh", "/app/docker-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--access-logfile", "-", "--error-logfile", "-"]
