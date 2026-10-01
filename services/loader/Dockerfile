FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY services/loader ./services/loader
ENV PORT=8080
CMD ["sh", "-c", "uvicorn services.loader.main:app --host 0.0.0.0 --port ${PORT}"]
