import http from 'k6/http';
import { check } from 'k6';

// Quick 1-minute test to get baseline metrics
export const options = {
  stages: [
    { duration: '10s', target: 10 },   // Ramp up
    { duration: '30s', target: 50 },   // Test at 50 concurrent users
    { duration: '20s', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<1000'], // Baseline: just checking current state
  }
};

export default function () {
  const response = http.post('http://localhost:8080/task', 
    JSON.stringify({
      persona_id: 'test',
      topic: 'Quick performance test',
      task_type: 'generate_post'
    }), {
      headers: { 'Content-Type': 'application/json' },
      timeout: '10s'
    }
  );
  
  check(response, {
    'status is 200': (r) => r.status === 200,
    'has response': (r) => r.body.length > 0
  });
}

export function handleSummary(data) {
  const p95 = Math.round(data.metrics.http_req_duration.values['p(95)']);
  const p99 = Math.round(data.metrics.http_req_duration.values['p(99)']);
  const rps = Math.round(data.metrics.http_reqs.values.rate);
  
  console.log('\n📊 QUICK BASELINE TEST RESULTS:');
  console.log('================================');
  console.log(`P95 Latency: ${p95}ms ${p95 < 400 ? '✅' : `❌ (Need ${400 - p95}ms improvement)`}`);
  console.log(`P99 Latency: ${p99}ms`);
  console.log(`Requests/sec: ${rps}`);
  console.log('');
  
  if (p95 > 400) {
    console.log('🔧 Optimizations needed:');
    console.log('1. Add Redis caching');
    console.log('2. Enable connection pooling');
    console.log('3. Implement request batching');
  } else {
    console.log('✅ Ready for full load test!');
  }
  
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true })
  };
}

import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';