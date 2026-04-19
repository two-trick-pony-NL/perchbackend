FROM python:3.10-buster

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen

COPY . .

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]