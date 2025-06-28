FROM python:3.11-slim

WORKDIR /app

# Copy source code
COPY . .

# Install FastAPI + Uvicorn + Mongo + AWS client
RUN pip install fastapi uvicorn[standard] motor boto3 pydantic[dotenv] clickhouse_connect

# Run FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]