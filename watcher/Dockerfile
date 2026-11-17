FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir kubernetes requests
COPY watcher.py .
USER 1000
CMD ["python", "watcher.py"]