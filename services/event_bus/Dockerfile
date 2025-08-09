FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy only Event Bus requirements
COPY services/event_bus/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Event Bus service code
COPY services/event_bus ./services/event_bus

# Set Python path for imports
ENV PYTHONPATH=/app

# Make run script executable
RUN chmod +x /app/services/event_bus/run.py

# Run the API server
CMD ["python", "/app/services/event_bus/run.py"]