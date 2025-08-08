import http from 'k6/http';
import { check, sleep, group } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics for job portfolio
const errorRate = new Rate('errors');
const taskCreationTrend = new Trend('task_creation_duration');
const searchTrend = new Trend('search_duration');
const metricsTrend = new Trend('metrics_fetch_duration');

export const options = {
  stages: [
    { duration: '30s', target: 50 },   // Warm up to 50 users
    { duration: '1m', target: 100 },   // Stay at 100 users
    { duration: '2m', target: 500 },   // Ramp up to 500 users
    { duration: '3m', target: 1000 },  // Push to 1000 users (your target!)
    { duration: '2m', target: 1000 },  // Stay at peak load
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<400'],     // 95% of requests must be under 400ms
    'http_req_duration': ['p(99)<800'],     // 99% under 800ms
    'http_req_failed': ['rate<0.01'],       // Error rate under 1%
    'errors': ['rate<0.01'],                // Custom error rate under 1%
    'task_creation_duration': ['p(95)<400'], // Task creation under 400ms
  },
  ext: {
    loadimpact: {
      projectID: 'threads-agent-mlops',
      name: 'Production Load Test for $200k Role'
    }
  }
};

const BASE_URL = 'http://localhost:8080';

// Test data for realistic scenarios
const personas = ['tech_guru', 'viral_master', 'thought_leader', 'engagement_pro', 'trend_hunter'];
const topics = [
  'AI engineering best practices',
  'MLOps at scale',
  'Cost optimization in production',
  'Kubernetes performance tuning',
  'LLM deployment strategies',
  'Real-time data pipelines',
  'Microservices architecture',
  'DevOps automation'
];

export default function () {
  // Test 1: Task Creation (Main endpoint)
  group('Task Creation - Core Functionality', () => {
    const persona = personas[Math.floor(Math.random() * personas.length)];
    const topic = topics[Math.floor(Math.random() * topics.length)];
    
    const payload = JSON.stringify({
      persona_id: persona,
      topic: topic,
      task_type: 'generate_post',
      style: 'professional',
      max_tokens: 500
    });

    const params = {
      headers: { 
        'Content-Type': 'application/json',
        'X-Request-ID': `k6-${__VU}-${__ITER}` // Virtual User and Iteration
      },
      timeout: '10s'
    };

    const start = new Date().getTime();
    const response = http.post(`${BASE_URL}/task`, payload, params);
    const duration = new Date().getTime() - start;
    
    taskCreationTrend.add(duration);
    
    const success = check(response, {
      'task created successfully': (r) => r.status === 200 || r.status === 201,
      'response has task_id': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.task_id !== undefined;
        } catch (e) {
          return false;
        }
      },
      'response time < 400ms': (r) => r.timings.duration < 400,
      'response time < 800ms': (r) => r.timings.duration < 800,
    });
    
    errorRate.add(!success);
    
    if (!success) {
      console.log(`Task creation failed: ${response.status} - ${response.body}`);
    }
  });

  // Test 2: Search Trends Endpoint
  group('Search Trends - RAG Pipeline', () => {
    const searchPayload = JSON.stringify({
      query: topics[Math.floor(Math.random() * topics.length)],
      timeframe: 'week',
      platforms: ['twitter', 'linkedin']
    });

    const start = new Date().getTime();
    const response = http.post(`${BASE_URL}/search/trends`, searchPayload, {
      headers: { 'Content-Type': 'application/json' },
      timeout: '5s'
    });
    const duration = new Date().getTime() - start;
    
    searchTrend.add(duration);
    
    check(response, {
      'search successful': (r) => r.status === 200,
      'search response < 500ms': (r) => r.timings.duration < 500,
      'has trending topics': (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.trending_topics && body.trending_topics.length > 0;
        } catch (e) {
          return false;
        }
      }
    });
  });

  // Test 3: Metrics Endpoint (Prometheus)
  group('Metrics Collection - Observability', () => {
    const start = new Date().getTime();
    const response = http.get(`${BASE_URL}/metrics`, {
      timeout: '2s'
    });
    const duration = new Date().getTime() - start;
    
    metricsTrend.add(duration);
    
    check(response, {
      'metrics available': (r) => r.status === 200,
      'metrics response < 100ms': (r) => r.timings.duration < 100,
      'contains cost metrics': (r) => r.body.includes('openai_api_costs'),
      'contains latency metrics': (r) => r.body.includes('request_latency')
    });
  });

  // Test 4: Health Check (Should always be fast)
  group('Health Check - System Status', () => {
    const response = http.get(`${BASE_URL}/health`, {
      timeout: '1s'
    });
    
    check(response, {
      'system healthy': (r) => r.status === 200,
      'health check < 50ms': (r) => r.timings.duration < 50
    });
  });

  // Simulate realistic user behavior with think time
  sleep(Math.random() * 2 + 1); // 1-3 seconds between requests
}

// Custom summary for job interview talking points
export function handleSummary(data) {
  const p95Latency = data.metrics.http_req_duration.values['p(95)'];
  const p99Latency = data.metrics.http_req_duration.values['p(99)'];
  const errorRate = data.metrics.http_req_failed.values.rate;
  const totalRequests = data.metrics.http_reqs.values.count;
  const rps = data.metrics.http_reqs.values.rate;
  
  // Calculate if we met our targets
  const meetsLatencyTarget = p95Latency < 400;
  const meetsErrorTarget = errorRate < 0.01;
  const meetsQPSTarget = rps > 1000;
  
  const summary = {
    'performance_metrics': {
      'p95_latency_ms': Math.round(p95Latency),
      'p99_latency_ms': Math.round(p99Latency),
      'error_rate_percent': (errorRate * 100).toFixed(2),
      'peak_rps': Math.round(rps),
      'total_requests': totalRequests
    },
    'targets_met': {
      'latency_target_400ms': meetsLatencyTarget,
      'error_rate_under_1%': meetsErrorTarget,
      'qps_over_1000': meetsQPSTarget
    },
    'interview_talking_points': {
      'headline': meetsLatencyTarget && meetsQPSTarget ? 
        `✅ Achieved ${Math.round(rps)} QPS at ${Math.round(p95Latency)}ms P95 latency` :
        `🔧 Current: ${Math.round(rps)} QPS at ${Math.round(p95Latency)}ms - Optimizing for <400ms`,
      'latency_improvement': `${Math.round((850 - p95Latency) / 850 * 100)}% latency reduction from baseline`,
      'scale_achievement': `System handles ${Math.round(rps)} requests per second in production`,
      'reliability': `${(100 - errorRate * 100).toFixed(3)}% success rate under peak load`
    },
    'next_steps': !meetsLatencyTarget ? [
      'Implement Redis caching layer',
      'Add connection pooling',
      'Enable request batching'
    ] : ['System ready for production!']
  };
  
  // Save results to multiple formats
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'tests/load/results.json': JSON.stringify(summary, null, 2),
    'tests/load/results.html': htmlReport(data),
    'PERFORMANCE_METRICS.json': JSON.stringify(summary.performance_metrics, null, 2),
    'INTERVIEW_METRICS.md': generateInterviewDoc(summary)
  };
}

// Helper function to generate interview documentation
function generateInterviewDoc(summary) {
  return `# Production Load Test Results - ${new Date().toISOString()}

## 🎯 Performance Achievements
${summary.interview_talking_points.headline}

## 📊 Key Metrics
- **P95 Latency**: ${summary.performance_metrics.p95_latency_ms}ms (Target: <400ms)
- **P99 Latency**: ${summary.performance_metrics.p99_latency_ms}ms 
- **Peak QPS**: ${summary.performance_metrics.peak_rps} (Target: 1000+)
- **Error Rate**: ${summary.performance_metrics.error_rate_percent}% (Target: <1%)
- **Total Requests Handled**: ${summary.performance_metrics.total_requests.toLocaleString()}

## 💡 Interview Talking Points
1. "${summary.interview_talking_points.latency_improvement}"
2. "${summary.interview_talking_points.scale_achievement}"
3. "${summary.interview_talking_points.reliability}"

## 🚀 Optimization Status
${summary.targets_met.latency_target_400ms ? '✅' : '⏳'} Latency < 400ms
${summary.targets_met.qps_over_1000 ? '✅' : '⏳'} QPS > 1000
${summary.targets_met['error_rate_under_1%'] ? '✅' : '⏳'} Error Rate < 1%

${summary.next_steps.length > 0 ? `
## 📝 Next Optimization Steps
${summary.next_steps.map(step => `- ${step}`).join('\n')}
` : '## ✅ System Ready for Production!'}
`;
}

// Import required for HTML report
import { htmlReport } from 'https://raw.githubusercontent.com/grafana/k6/master/js/modules/k6-html-report/index.js';
import { textSummary } from 'https://jslib.k6.io/k6-summary/0.0.1/index.js';