FROM python:3.11-alpine

WORKDIR /app

# Install system dependencies for Python package compilation
RUN apk add --no-cache build-base libffi-dev openssl-dev cargo

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY mcp_server.py .
COPY dingo ./dingo/

# Create outputs directory
RUN mkdir -p /app/outputs && chmod 777 /app/outputs

# Ensure Python output is sent straight to stdout
ENV PYTHONUNBUFFERED=1

# Command will be provided by smithery.yaml commandFunction
CMD ["python", "mcp_server.py"]
