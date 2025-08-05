#!/bin/bash

echo "🧪 TESTING LIVE ACHIEVEMENT-COLLECTOR INTEGRATION"
echo "================================================="

BASE_URL="http://localhost:8090"

# Test 1: Health check
echo -e "\n1️⃣ Health Check"
curl -s $BASE_URL/health | jq '.'

# Test 2: Test new integration endpoints
echo -e "\n2️⃣ Testing /tech-doc-integration/content-ready"
curl -s $BASE_URL/tech-doc-integration/content-ready?limit=5 -X GET

echo -e "\n\n3️⃣ Testing /tech-doc-integration/recent-highlights"
curl -s -X POST $BASE_URL/tech-doc-integration/recent-highlights \
  -H "Content-Type: application/json" \
  -d '{}' \
  --url-query "days=30" \
  --url-query "min_impact_score=70" \
  --url-query "limit=5"

echo -e "\n\n4️⃣ Testing /tech-doc-integration/batch-get"
curl -s -X POST $BASE_URL/tech-doc-integration/batch-get \
  -H "Content-Type: application/json" \
  -d '{"achievement_ids": [27]}'

echo -e "\n\n5️⃣ Testing /tech-doc-integration/company-targeted"
curl -s -X POST $BASE_URL/tech-doc-integration/company-targeted \
  -H "Content-Type: application/json" \
  -d '{}' \
  --url-query "company_name=anthropic" \
  --url-query "limit=3"

echo -e "\n\n6️⃣ Testing /tech-doc-integration/stats/content-opportunities"
curl -s $BASE_URL/tech-doc-integration/stats/content-opportunities

echo -e "\n\n✅ Integration test complete!"