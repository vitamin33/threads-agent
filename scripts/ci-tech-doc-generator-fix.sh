#!/bin/bash
# Fix for CI tech-doc-generator ImagePullBackOff issue
# This script creates a minimal placeholder image for CI testing

set -e

echo "🔧 Creating placeholder tech-doc-generator image for CI..."

# Create minimal Dockerfile for placeholder
cat > /tmp/Dockerfile.placeholder << 'EOF'
FROM python:3.12-slim
WORKDIR /app
RUN pip install fastapi uvicorn
COPY << 'PYEOF' /app/main.py
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok", "service": "tech-doc-generator-placeholder"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
PYEOF

EXPOSE 8080
CMD ["python", "main.py"]
EOF

# Build placeholder image
echo "📦 Building placeholder image..."
docker build -f /tmp/Dockerfile.placeholder -t tech-doc-generator:local /tmp/

# Check if we're in k3d environment and import
if command -v k3d &> /dev/null && k3d cluster list | grep -q "dev"; then
    echo "📥 Importing to k3d cluster..."
    k3d image import tech-doc-generator:local -c dev
    echo "✅ Placeholder image imported to k3d cluster"
else
    echo "⚠️ k3d cluster 'dev' not found - image built locally only"
fi

echo "🎉 tech-doc-generator placeholder ready for CI"

# Cleanup
rm -f /tmp/Dockerfile.placeholder