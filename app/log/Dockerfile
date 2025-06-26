FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn[standard] gunicorn boto3 motor pydantic[dotenv]
CMD ["gunicorn", "main:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "4", "--bind", "0.0.0.0:80"]