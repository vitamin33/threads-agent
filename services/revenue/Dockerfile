FROM python:3.12-slim-bookworm

WORKDIR /app

# Install dependencies
COPY services/revenue/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy common modules
COPY services/common /app/services/common

# Copy revenue service
COPY services/revenue /app/services/revenue

# Set environment variables
ENV PYTHONPATH=/app

# Run the service
CMD ["uvicorn", "services.revenue.main:app", "--host", "0.0.0.0", "--port", "8080"]