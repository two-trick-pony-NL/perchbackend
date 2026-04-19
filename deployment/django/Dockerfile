FROM python:3.10-buster

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# install uv
RUN pip install uv

# copy dependency files first (better caching)
COPY pyproject.toml uv.lock* ./

# install dependencies
RUN uv sync --frozen

# copy project
COPY . .

# run uwsgi
CMD ["uwsgi", "--http", "0.0.0.0:8000", \
      "--protocol", "uwsgi", \
      "--wsgi", "core.wsgi:application"]