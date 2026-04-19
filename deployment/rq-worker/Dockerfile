FROM python:3.10-buster

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV REDIS_URL=redis://localhost:6379
ENV DJANGO_SETTINGS_MODULE=core.settings

# install uv
RUN pip install uv

WORKDIR /app

# copy only dependency files first (better caching)
COPY pyproject.toml uv.lock* ./

# install deps into environment
RUN uv sync --frozen
RUN pip install requirements.txt

# copy app code
COPY . .

CMD ["python", "manage.py", "rqworker", "default"]