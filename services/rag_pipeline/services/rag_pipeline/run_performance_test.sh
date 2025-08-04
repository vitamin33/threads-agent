#!/bin/bash
set -e

echo "🚀 RAG Pipeline Performance Testing Script"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if RAG pipeline is deployed
echo -e "\n${YELLOW}Checking if RAG pipeline is deployed...${NC}"
if kubectl get pods -l app=rag-pipeline 2>/dev/null | grep -q Running; then
    echo -e "${GREEN}✓ RAG pipeline is running${NC}"
else
    echo -e "${RED}✗ RAG pipeline not found. Deploying...${NC}"
    
    # Deploy RAG pipeline
    echo "Deploying RAG pipeline to k3d..."
    kubectl apply -f services/rag_pipeline/k8s/deployment.yaml
    
    # Wait for deployment
    echo "Waiting for pods to be ready..."
    kubectl wait --for=condition=ready pod -l app=rag-pipeline --timeout=300s
fi

# Check port forwarding
echo -e "\n${YELLOW}Setting up port forwarding...${NC}"
# Kill any existing port forward
pkill -f "port-forward.*rag-pipeline" || true
sleep 2

# Start port forwarding in background
kubectl port-forward svc/rag-pipeline 8000:8000 &
PF_PID=$!
echo "Port forwarding started (PID: $PF_PID)"

# Wait for port to be ready
echo "Waiting for service to be accessible..."
for i in {1..30}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is ready${NC}"
        break
    fi
    echo -n "."
    sleep 1
done

# Ingest some test data first
echo -e "\n${YELLOW}Ingesting test data...${NC}"
python3 -c "
import requests
import json

# Ingest some documents for realistic testing
documents = [
    {
        'id': f'test-doc-{i}',
        'content': f'''
        Machine learning is a subset of artificial intelligence that focuses on 
        the development of algorithms and statistical models that enable computer 
        systems to improve their performance on tasks through experience. 
        Document {i} contains information about {topic}.
        ''',
        'metadata': {'source': 'test', 'topic': topic}
    }
    for i, topic in enumerate([
        'neural networks', 'deep learning', 'transformers',
        'embeddings', 'vector databases', 'RAG systems',
        'LLMs', 'fine-tuning', 'prompt engineering', 'MLOps'
    ])
]

response = requests.post(
    'http://localhost:8000/api/v1/ingest',
    json={
        'documents': documents,
        'chunk_size': 500,
        'chunk_overlap': 50
    }
)

if response.status_code == 200:
    result = response.json()
    print(f'✓ Ingested {result[\"ingested_documents\"]} documents')
    print(f'  Created {result[\"total_chunks\"]} chunks')
else:
    print(f'✗ Ingestion failed: {response.status_code}')
"

# Run the performance benchmark
echo -e "\n${YELLOW}Running performance benchmark...${NC}"
echo "This will take approximately 3-5 minutes"
echo "----------------------------------------"

cd services/rag_pipeline
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate
pip install aiohttp numpy > /dev/null 2>&1

# Run the benchmark
python tests/performance/performance_benchmark.py

# Cleanup
echo -e "\n${YELLOW}Cleaning up...${NC}"
kill $PF_PID 2>/dev/null || true

echo -e "\n${GREEN}✅ Performance testing complete!${NC}"
echo "Check 'rag_performance_report.md' for detailed results"