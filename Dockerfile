FROM python:3.12-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PORT=8000
COPY pyproject.toml README.md tokens.css ./
COPY src ./src
COPY seed ./seed
RUN pip install --no-cache-dir . && useradd --create-home app && chown -R app:app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn objection_winmap.main:app --host 0.0.0.0 --port ${PORT}"]
