FROM python:3.13-slim

WORKDIR /app

RUN pip install gunicorn==23.0.0

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/backend_media && chmod 777 /app/backend_media && python3 manage.py collectstatic --noinput

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "core.wsgi"]