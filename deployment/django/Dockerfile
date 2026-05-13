FROM python:3.10-buster

EXPOSE 8000/tcp

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app


RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY . .

RUN chmod +x deployment/django/entrypoint.sh

CMD ["deployment/django/entrypoint.sh"]