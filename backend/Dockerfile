FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=2.0,<3.0"

# En local se pueden instalar también las dependencias de tests
ARG INSTALL_DEV=false
COPY pyproject.toml poetry.lock ./
RUN if [ "$INSTALL_DEV" = "true" ]; then poetry install --no-root; else poetry install --only main --no-root; fi

COPY . .
RUN DJANGO_SECRET_KEY=solo-para-build python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["sh", "start.sh"]
