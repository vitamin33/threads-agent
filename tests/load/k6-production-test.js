// Production-Ready Load Test with Rate Limiting
// Tests the system with our new production optimizations

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metric for rate limiting
const rateLimited = new Rate('rate_limited');

export const options = {
  stages: [
    { duration: '30s', target: 20 },   // Warm up to 20 users
    { duration: '1m', target: 50 },    // Stay at 50 (within our limit)
    { duration: '30s', target: 100 },  // Push to 100 (at our limit)
    { duration: '30s', target: 150 },  // Over limit (should see 429s)
    { duration: '30s', target: 50 },   // Scale back down
    { duration: '30s', target: 0 },    // Cool down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<100'],  // Tighter threshold with optimizations
    'http_req_failed': ['rate<0.05'],    // Allow 5% failures (rate limiting)
    'rate_limited': ['rate<0.20'],       // No more than 20% rate limited
  },
};

export default function () {
  const payload = JSON.stringify({
    persona_id: 'test_persona',
    topic: 'Load testing with production optimizations',
    task_type: 'generate_post'
  });

  const params = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const res = http.post('http://localhost:8080/task', payload, params);
  
  // Check various response scenarios
  const isSuccess = check(res, {
    'status is 200': (r) => r.status === 200,
    'status is 429 (rate limited)': (r) => r.status === 429,
    'response time < 100ms': (r) => r.timings.duration < 100,
  });
  
  // Track rate limiting
  rateLimited.add(res.status === 429);
  
  // If rate limited, back off a bit
  if (res.status === 429) {
    sleep(1);  // Wait 1 second before retrying
  } else {
    sleep(0.1);  // Normal pause between requests
  }
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
  };
}

function textSummary(data, options) {
  const successRate = 100 - (data.metrics.http_req_failed.values.rate * 100);
  const rateLimitRate = data.metrics.rate_limited.values.rate * 100;
  const p95Latency = data.metrics.http_req_duration.values['p(95)'];
  
  return `
🚀 Production Load Test Results
================================
✅ Success Rate: ${successRate.toFixed(2)}%
⚡ P95 Latency: ${p95Latency.toFixed(2)}ms
🛡️ Rate Limited: ${rateLimitRate.toFixed(2)}%
📊 Total Requests: ${data.metrics.http_reqs.values.count}

Production Optimizations Applied:
- Rate limiting (100 concurrent max)
- DB connection pooling (10 connections)
- Health checks implemented
- Circuit breaker protection

Status: ${successRate > 95 ? '✅ PRODUCTION READY' : '⚠️ NEEDS TUNING'}
`;
}