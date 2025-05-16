FROM python:3.11-bullseye

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker cache
COPY requirements/runtime.txt ./requirements/
COPY setup.cfg .

# Update pip and install only runtime dependencies
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements/runtime.txt

# Copy application code after installing dependencies to avoid reinstalling when code changes
COPY mcp_server.py .
COPY dingo ./dingo/
COPY test ./test/
COPY examples ./examples/
COPY smithery.yaml .

# Create data output directory with appropriate permissions
RUN mkdir -p /app/outputs && chmod 777 /app/outputs

# Ensure Python output is sent directly to stdout without buffering
ENV PYTHONUNBUFFERED=1

# Use Smithery deployment mode by default in container
ENV LOCAL_DEPLOYMENT_MODE=true

# Startup command (specific parameters provided by smithery.yaml commandFunction)
CMD ["python", "mcp_server.py"]
