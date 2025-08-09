#!/bin/bash
# Test fake-threads image locally to verify it works

set -e

echo "🧪 Testing fake-threads image locally..."

# Check if image exists
if ! docker images | grep -q "fake-threads.*local"; then
    echo "❌ fake-threads:local image not found. Building..."
    docker build -f services/fake_threads/Dockerfile -t fake-threads:local .
fi

echo "🏃 Running fake-threads container..."
docker run -d --name test-fake-threads -p 9009:9009 fake-threads:local

echo "⏳ Waiting for container to start..."
sleep 5

echo "🔍 Container status:"
docker ps -a | grep test-fake-threads

echo "📝 Container logs:"
docker logs test-fake-threads

echo "🏥 Testing health endpoint:"
curl -f http://localhost:9009/health || {
    echo "❌ Health check failed!"
    echo "📋 Full container logs:"
    docker logs test-fake-threads
    docker rm -f test-fake-threads
    exit 1
}

echo "✅ fake-threads container is working correctly!"

# Cleanup
docker rm -f test-fake-threads

echo "🎯 Test complete - fake-threads image is functional"