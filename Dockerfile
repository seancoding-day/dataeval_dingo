FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY requirements/ ./requirements/
COPY requirements.txt .
COPY setup.cfg .

# Update pip and install project dependencies
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code after installing dependencies to avoid reinstalling when code changes
COPY mcp_server.py .
COPY dingo ./dingo/
COPY smithery.yaml .

# Create data output directory
RUN mkdir -p /app/outputs && chmod 777 /app/outputs

# Ensure Python output is sent directly to stdout without buffering
ENV PYTHONUNBUFFERED=1

# Startup command (specific parameters provided by smithery.yaml commandFunction)
CMD ["python", "mcp_server.py"]
