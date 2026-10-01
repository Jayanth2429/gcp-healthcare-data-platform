FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY services/ingestor ./services/ingestor
ENV PORT=8080
CMD ["sh", "-c", "uvicorn services.ingestor.main:app --host 0.0.0.0 --port ${PORT}"]
