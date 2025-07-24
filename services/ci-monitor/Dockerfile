FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    make \
    && rm -rf /var/lib/apt/lists/*

# Install Just command runner (used by the project)
RUN curl -qfsSL https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY monitor_v3.py .
COPY monitor_v2.py .
COPY monitor.py .

# Set up git config
RUN git config --global user.email "ci-bot@threads-agent.com" && \
    git config --global user.name "CI Auto-Fix Bot"

# Use the enhanced monitor by default
CMD ["python", "monitor_v3.py"]