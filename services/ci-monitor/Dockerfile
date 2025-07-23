FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN curl -fsSL https://claude.ai/install.sh | sh

# Install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY monitor.py .
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Set up git config
RUN git config --global user.email "ci-bot@threads-agent.com" && \
    git config --global user.name "CI Auto-Fix Bot"

ENTRYPOINT ["./entrypoint.sh"]