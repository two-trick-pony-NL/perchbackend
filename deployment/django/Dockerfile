FROM python:3.10-buster

EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install uv
RUN pip install --upgrade pip


COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen
RUN uv pip freeze > requirements.txt
RUN pip install -r requirements.txt


COPY . .

CMD ["gunicorn", "core.wsgi:application", "--bind", "0.0.0.0:8000"]