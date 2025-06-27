FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install fastapi uvicorn[standard] boto3 motor pydantic[dotenv]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]