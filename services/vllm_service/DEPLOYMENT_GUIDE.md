# vLLM Service - Production Deployment Guide

## Executive Summary

**Complete production deployment guide for vLLM service on Kubernetes with Apple Silicon optimization. Includes auto-scaling, monitoring, cost optimization, and disaster recovery for enterprise environments.**

**Deployment Highlights:**
- ✅ **Kubernetes Native**: Production-ready Helm charts with auto-scaling
- ✅ **Apple Silicon Optimized**: M-series node affinity and MPS acceleration
- ✅ **Enterprise Security**: RBAC, network policies, and security contexts
- ✅ **Full Observability**: Prometheus, Grafana, Jaeger, and AlertManager integration
- ✅ **Cost Optimization**: Resource efficiency and intelligent scaling policies

---

## Prerequisites

### Infrastructure Requirements

**Minimum Requirements (Development)**
```yaml
Resources:
  CPU: 2 cores (Apple Silicon M1 or newer)
  Memory: 8GB RAM
  Storage: 50GB SSD
  Network: 1Gbps

Software:
  Kubernetes: 1.24+
  Helm: 3.8+
  Docker: 20.10+
  kubectl: 1.24+
```

**Production Requirements (Recommended)**
```yaml
Resources:
  CPU: 8 cores (Apple Silicon M3/M4 Max preferred)
  Memory: 32GB unified memory
  Storage: 200GB NVMe SSD
  Network: 10Gbps

Node Configuration:
  Min Nodes: 3 (high availability)
  Max Nodes: 10 (auto-scaling)
  Node Type: Apple Silicon (arm64)
  
Security:
  Pod Security Standards: Restricted
  Network Policies: Enabled
  RBAC: Enabled with least privilege
```

### Apple Silicon Cluster Setup

**1. Create Apple Silicon Kubernetes Cluster**
```bash
# Using k3d for local development
k3d cluster create vllm-cluster \
  --image rancher/k3s:v1.27.4-k3s1 \
  --port "8080:80@loadbalancer" \
  --port "8443:443@loadbalancer" \
  --agents 3 \
  --k3s-arg "--disable=traefik@server:0" \
  --k3s-arg "--node-label=kubernetes.io/arch=arm64@server:0" \
  --k3s-arg "--node-label=node.threads-agent.com/apple-silicon=true@server:0"

# Verify cluster
kubectl get nodes -o wide
kubectl describe nodes | grep -A 5 "Labels"
```

**2. Install Required Components**
```bash
# Install Prometheus Operator
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm install prometheus-stack prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set grafana.enabled=true \
  --set grafana.adminPassword=admin123 \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi

# Install Jaeger for distributed tracing  
helm repo add jaegertracing https://jaegertracing.github.io/helm-charts
helm install jaeger jaegertracing/jaeger \
  --namespace observability \
  --create-namespace \
  --set allInOne.enabled=true

# Verify installations
kubectl get pods -n monitoring
kubectl get pods -n observability
```

---

## Deployment Architecture

### Production Deployment Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Production Kubernetes Cluster                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │  Load Balancer  │    │   vLLM Service  │    │    Monitoring   │     │
│  │                 │    │                 │    │                 │     │
│  │ • Nginx Ingress │────│ • 3 Replicas    │────│ • Prometheus    │     │
│  │ • Rate Limiting │    │ • Apple Silicon │    │ • Grafana       │     │
│  │ • TLS Termination   │ • Auto Scaling  │    │ • AlertManager  │     │
│  │ • Health Checks │    │ • Circuit Break │    │ • Jaeger        │     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│           │                       │                       │             │
│           │                       │                       │             │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐     │
│  │   Cert Manager  │    │   Persistent    │    │   Network       │     │
│  │                 │    │   Storage       │    │   Policies      │     │
│  │ • TLS Certs     │    │                 │    │                 │     │
│  │ • Auto Renewal  │    │ • Model Cache   │    │ • Ingress Rules │     │
│  │ • Let's Encrypt │    │ • Metrics DB    │    │ • Pod-to-Pod    │     │
│  │                 │    │ • Logs Storage  │    │ • Egress Control│     │
│  └─────────────────┘    └─────────────────┘    └─────────────────┘     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘

              │                         │                         │
              ▼                         ▼                         ▼
    
┌─────────────────────┐   ┌─────────────────────┐   ┌─────────────────────┐
│    Apple Silicon    │   │     Auto Scaling    │   │   Disaster Recovery │
│    Node Pool        │   │     Policies        │   │     Strategy        │
│                     │   │                     │   │                     │
│ • M3/M4 Max Nodes   │   │ • CPU-based HPA     │   │ • Multi-AZ Deploy   │
│ • MPS Acceleration  │   │ • Custom Metrics    │   │ • Backup Strategy   │
│ • Unified Memory    │   │ • Predictive Scale  │   │ • Failover Process  │
│ • Power Efficiency  │   │ • Cost Optimization │   │ • RTO/RPO Targets   │
└─────────────────────┘   └─────────────────────┘   └─────────────────────┘
```

---

## Helm Chart Deployment

### 1. vLLM Service Helm Chart

**Create Helm Chart Structure**
```bash
# Create chart directory
mkdir -p vllm-service-chart/templates
cd vllm-service-chart

# Chart.yaml
cat > Chart.yaml << 'EOF'
apiVersion: v2
name: vllm-service
description: High-performance vLLM service with Apple Silicon optimization
type: application
version: 1.0.0
appVersion: "1.0.0"
home: https://github.com/threads-agent-stack/threads-agent
maintainers:
  - name: GenAI Team
    email: team@threads-agent-stack.com
keywords:
  - vllm
  - llm
  - ai
  - apple-silicon
  - cost-optimization
dependencies:
  - name: prometheus
    version: "15.x"
    repository: "https://prometheus-community.github.io/helm-charts"
    condition: prometheus.enabled
EOF
```

**Values Configuration (values.yaml)**
```yaml
# vLLM Service Configuration
replicaCount: 3
image:
  repository: threads-agent/vllm-service
  pullPolicy: IfNotPresent
  tag: "latest"

# Apple Silicon Optimization
nodeSelector:
  kubernetes.io/arch: arm64
  node.threads-agent.com/apple-silicon: "true"

resources:
  requests:
    memory: "8Gi"
    cpu: "2000m"
    ephemeral-storage: "10Gi"
  limits:
    memory: "16Gi"
    cpu: "4000m"
    ephemeral-storage: "20Gi"

# Auto Scaling Configuration
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  
  # Custom metrics for <50ms SLI
  customMetrics:
    - type: Pods
      pods:
        metric:
          name: vllm_request_duration_seconds_p95
        target:
          type: AverageValue
          averageValue: "0.05"  # 50ms SLI target

# Service Configuration
service:
  type: ClusterIP
  port: 8090
  targetPort: 8090
  annotations:
    prometheus.io/scrape: "true"
    prometheus.io/port: "8090"
    prometheus.io/path: "/metrics"

# Ingress Configuration
ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/rate-limit: "1000"
    nginx.ingress.kubernetes.io/rate-limit-window: "1m"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
  hosts:
    - host: vllm.threads-agent-stack.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: vllm-service-tls
      hosts:
        - vllm.threads-agent-stack.com

# Health Check Configuration
healthcheck:
  livenessProbe:
    httpGet:
      path: /health
      port: 8090
    initialDelaySeconds: 60
    periodSeconds: 30
    timeoutSeconds: 10
    failureThreshold: 3
    successThreshold: 1
  
  readinessProbe:
    httpGet:
      path: /performance/latency
      port: 8090
    initialDelaySeconds: 30
    periodSeconds: 10
    timeoutSeconds: 5
    failureThreshold: 2
    successThreshold: 1

# Security Configuration
securityContext:
  runAsNonRoot: true
  runAsUser: 10001
  runAsGroup: 10001
  fsGroup: 10001
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true

podSecurityContext:
  seccompProfile:
    type: RuntimeDefault

# Network Policy
networkPolicy:
  enabled: true
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: threads-agent-stack
      - namespaceSelector:
          matchLabels:
            name: monitoring
      ports:
      - protocol: TCP
        port: 8090
  egress:
    - to: []
      ports:
      - protocol: TCP
        port: 443  # HTTPS outbound
      - protocol: TCP  
        port: 53   # DNS

# Environment Variables
env:
  VLLM_MODEL: "meta-llama/Llama-3.1-8B-Instruct"
  APPLE_SILICON_OPTIMIZATION: "true"
  MPS_ACCELERATION: "true"
  PROMETHEUS_METRICS_ENABLED: "true"
  COST_TRACKING_ENABLED: "true"
  CIRCUIT_BREAKER_ENABLED: "true"
  
# Persistent Volume for Model Cache
persistence:
  enabled: true
  storageClass: "fast-ssd"
  size: 50Gi
  accessModes:
    - ReadWriteOnce
  mountPath: /app/model_cache

# Monitoring Configuration
monitoring:
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
    path: /metrics
    
  prometheusRule:
    enabled: true
    rules:
      - alert: vLLMServiceDown
        expr: up{job="vllm-service"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "vLLM service is down"
          
      - alert: vLLMLatencyHigh
        expr: vllm_request_duration_seconds_p95 > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "vLLM latency exceeds 50ms target"
          
      - alert: vLLMQualityDegraded
        expr: avg(vllm_quality_score) < 0.85
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "vLLM quality score below threshold"

# Cost Optimization
costOptimization:
  enabled: true
  policies:
    - name: "apple-silicon-preference"
      weight: 100
      nodeAffinity:
        requiredDuringSchedulingIgnoredDuringExecution:
          nodeSelectorTerms:
          - matchExpressions:
            - key: node.threads-agent.com/apple-silicon
              operator: In
              values: ["true"]
    
    - name: "resource-efficiency"
      resources:
        requests:
          memory: "8Gi"
          cpu: "2000m"
        limits:
          memory: "16Gi"
          cpu: "4000m"
```

**Deployment Template (templates/deployment.yaml)**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "vllm-service.fullname" . }}
  labels:
    {{- include "vllm-service.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "vllm-service.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
        prometheus.io/scrape: "true"
        prometheus.io/port: "8090"
        prometheus.io/path: "/metrics"
      labels:
        {{- include "vllm-service.selectorLabels" . | nindent 8 }}
    spec:
      {{- with .Values.nodeSelector }}
      nodeSelector:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
        
      containers:
      - name: {{ .Chart.Name }}
        securityContext:
          {{- toYaml .Values.securityContext | nindent 12 }}
        image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
        imagePullPolicy: {{ .Values.image.pullPolicy }}
        
        ports:
        - name: http
          containerPort: 8090
          protocol: TCP
        - name: metrics
          containerPort: 9090
          protocol: TCP
          
        env:
        {{- range $key, $value := .Values.env }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
        
        resources:
          {{- toYaml .Values.resources | nindent 12 }}
          
        livenessProbe:
          {{- toYaml .Values.healthcheck.livenessProbe | nindent 12 }}
          
        readinessProbe:
          {{- toYaml .Values.healthcheck.readinessProbe | nindent 12 }}
          
        volumeMounts:
        {{- if .Values.persistence.enabled }}
        - name: model-cache
          mountPath: {{ .Values.persistence.mountPath }}
        {{- end }}
        - name: tmp
          mountPath: /tmp
        - name: var-tmp
          mountPath: /var/tmp
          
      volumes:
      {{- if .Values.persistence.enabled }}
      - name: model-cache
        persistentVolumeClaim:
          claimName: {{ include "vllm-service.fullname" . }}-pvc
      {{- end }}
      - name: tmp
        emptyDir: {}
      - name: var-tmp
        emptyDir: {}
```

### 2. Deploy vLLM Service

```bash
# Add threads-agent Helm repository
helm repo add threads-agent https://helm.threads-agent-stack.com
helm repo update

# Create namespace
kubectl create namespace vllm-service

# Deploy with custom values
helm install vllm-service threads-agent/vllm-service \
  --namespace vllm-service \
  --values production-values.yaml \
  --wait \
  --timeout 10m

# Verify deployment
kubectl get pods -n vllm-service
kubectl get svc -n vllm-service
kubectl get ingress -n vllm-service

# Check health
kubectl port-forward -n vllm-service svc/vllm-service 8090:8090 &
curl http://localhost:8090/health
```

---

## Production Configuration

### 1. Apple Silicon Node Configuration

**Node Labels and Taints**
```bash
# Label Apple Silicon nodes
kubectl label nodes <node-name> node.threads-agent.com/apple-silicon=true
kubectl label nodes <node-name> node.threads-agent.com/gpu-type=mps
kubectl label nodes <node-name> kubernetes.io/arch=arm64

# Optional: Taint nodes for dedicated vLLM workloads
kubectl taint nodes <node-name> workload=vllm:NoSchedule
```

**Apple Silicon Optimization ConfigMap**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: apple-silicon-config
  namespace: vllm-service
data:
  apple-silicon.yaml: |
    # Apple Silicon Optimization Configuration
    mps_acceleration: true
    unified_memory_optimization: true
    neural_engine_fallback: false
    power_efficiency_mode: "balanced"
    
    # Model Configuration
    model_precision: "bfloat16"
    quantization: "fp8"
    tensor_parallel_size: 1
    
    # Performance Tuning
    max_batch_size: 32
    max_sequence_length: 4096
    gpu_memory_utilization: 0.8
    
    # Caching Strategy
    response_cache_size: 10000
    model_cache_enabled: true
    cache_ttl_seconds: 3600
```

### 2. Auto-scaling Configuration

**Horizontal Pod Autoscaler**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-service-hpa
  namespace: vllm-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-service
  minReplicas: 3
  maxReplicas: 10
  
  metrics:
  # CPU-based scaling
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
        
  # Memory-based scaling
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
        
  # Custom metric: <50ms SLI compliance
  - type: Pods
    pods:
      metric:
        name: vllm_request_duration_seconds_p95
      target:
        type: AverageValue
        averageValue: "0.05"
        
  # Request rate scaling
  - type: Pods
    pods:
      metric:
        name: vllm_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"

  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
      selectPolicy: Max
      
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 25
        periodSeconds: 60
      selectPolicy: Min
```

**Vertical Pod Autoscaler (VPA)**
```yaml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: vllm-service-vpa
  namespace: vllm-service
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-service
  updatePolicy:
    updateMode: "Auto"
  resourcePolicy:
    containerPolicies:
    - containerName: vllm-service
      maxAllowed:
        cpu: 8000m
        memory: 32Gi
      minAllowed:
        cpu: 1000m
        memory: 4Gi
      controlledResources: ["cpu", "memory"]
```

### 3. Advanced Monitoring Setup

**ServiceMonitor for Prometheus**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: vllm-service-monitor
  namespace: vllm-service
  labels:
    app: vllm-service
    release: prometheus-stack
spec:
  selector:
    matchLabels:
      app: vllm-service
  endpoints:
  - port: metrics
    interval: 30s
    scrapeTimeout: 10s
    path: /metrics
    honorLabels: true
    
  namespaceSelector:
    matchNames:
    - vllm-service
```

**Prometheus Rules**
```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: vllm-service-rules
  namespace: vllm-service
spec:
  groups:
  - name: vllm-service.rules
    rules:
    # SLI: <50ms latency target
    - alert: vLLMLatencyTargetMissed
      expr: vllm_request_duration_seconds_p95 > 0.05
      for: 5m
      labels:
        severity: warning
        component: vllm-service
      annotations:
        summary: "vLLM service latency exceeds 50ms target"
        description: "P95 latency is {{ $value }}s, exceeding 50ms SLI target"
        runbook_url: "https://docs.threads-agent-stack.com/runbooks/vllm-latency"
        
    # SLI: Quality score maintenance  
    - alert: vLLMQualityDegraded
      expr: avg(vllm_quality_score) < 0.85
      for: 10m
      labels:
        severity: warning
        component: vllm-service
      annotations:
        summary: "vLLM quality score below threshold"
        description: "Average quality score is {{ $value }}, below 0.85 target"
        
    # SLI: Cost savings monitoring
    - alert: vLLMCostSavingsReduced
      expr: rate(vllm_cost_savings_usd[1h]) < 100
      for: 15m
      labels:
        severity: info
        component: vllm-service
      annotations:
        summary: "vLLM cost savings reduced"
        description: "Hourly cost savings rate is ${{ $value }}, below expected"
        
    # Circuit breaker monitoring
    - alert: vLLMCircuitBreakerOpen
      expr: vllm_circuit_breaker_open_total > 0
      for: 1m
      labels:
        severity: critical
        component: vllm-service
      annotations:
        summary: "vLLM circuit breaker is open"
        description: "Circuit breaker triggered, service degraded"
        
    # Apple Silicon optimization monitoring
    - alert: vLLMAppleSiliconNotOptimized
      expr: rate(vllm_apple_silicon_requests_total[5m]) / rate(vllm_requests_total[5m]) < 0.95
      for: 10m
      labels:
        severity: warning
        component: vllm-service
      annotations:
        summary: "vLLM not fully utilizing Apple Silicon optimization"
        description: "Only {{ $value | humanizePercentage }} of requests using Apple Silicon optimization"
```

### 4. Security Configuration

**Pod Security Policy**
```yaml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: vllm-service-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'projected'
    - 'secret'
    - 'downwardAPI'
    - 'persistentVolumeClaim'
  runAsUser:
    rule: 'MustRunAsNonRoot'
  runAsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 10001
        max: 65535
  fsGroup:
    rule: 'MustRunAs'
    ranges:
      - min: 10001
        max: 65535
  seLinux:
    rule: 'RunAsAny'
  readOnlyRootFilesystem: true
```

**Network Policy**
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: vllm-service-netpol
  namespace: vllm-service
spec:
  podSelector:
    matchLabels:
      app: vllm-service
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  # Allow ingress from nginx ingress controller
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8090
      
  # Allow monitoring from prometheus
  - from:
    - namespaceSelector:
        matchLabels:
          name: monitoring
    ports:
    - protocol: TCP
      port: 8090
      
  # Allow health checks from kube-system
  - from:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: TCP
      port: 8090
      
  egress:
  # Allow DNS resolution
  - to: []
    ports:
    - protocol: UDP
      port: 53
    - protocol: TCP
      port: 53
      
  # Allow HTTPS outbound (for model downloads)
  - to: []
    ports:
    - protocol: TCP
      port: 443
      
  # Allow internal cluster communication
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 6443  # Kubernetes API
```

---

## Monitoring and Observability

### 1. Grafana Dashboard Configuration

**vLLM Executive Dashboard**
```json
{
  "dashboard": {
    "title": "vLLM Service - Executive Dashboard",
    "tags": ["vllm", "executive", "cost-savings"],
    "panels": [
      {
        "title": "Cost Savings (Monthly Projection)",
        "type": "gauge",
        "targets": [{
          "expr": "rate(vllm_cost_savings_usd[1h]) * 24 * 30",
          "legendFormat": "Monthly Savings"
        }],
        "fieldConfig": {
          "max": 20000,
          "min": 0,
          "unit": "currencyUSD",
          "thresholds": [
            {"value": 0, "color": "red"},
            {"value": 5000, "color": "yellow"},
            {"value": 10000, "color": "green"}
          ]
        }
      },
      {
        "title": "Performance SLI Compliance",
        "type": "stat",
        "targets": [{
          "expr": "(rate(vllm_latency_target_met_total[1h]) / rate(vllm_requests_total[1h])) * 100",
          "legendFormat": "% Requests < 50ms"
        }],
        "fieldConfig": {
          "max": 100,
          "min": 0,
          "unit": "percent"
        }
      },
      {
        "title": "Quality Score Trend",
        "type": "timeseries",
        "targets": [{
          "expr": "avg(vllm_quality_score)",
          "legendFormat": "Quality Score"
        }],
        "fieldConfig": {
          "custom": {
            "thresholdsStyle": {"mode": "line"},
            "thresholds": [{"value": 0.85, "color": "green"}]
          }
        }
      }
    ]
  }
}
```

**vLLM Technical Operations Dashboard**
```json
{
  "dashboard": {
    "title": "vLLM Service - Technical Operations",
    "tags": ["vllm", "operations", "sre"],
    "panels": [
      {
        "title": "Request Rate",
        "type": "timeseries",
        "targets": [{
          "expr": "rate(vllm_requests_total[1m])",
          "legendFormat": "Requests/sec"
        }]
      },
      {
        "title": "Latency Percentiles",
        "type": "timeseries", 
        "targets": [
          {"expr": "histogram_quantile(0.50, rate(vllm_request_duration_seconds_bucket[5m]))", "legendFormat": "P50"},
          {"expr": "histogram_quantile(0.95, rate(vllm_request_duration_seconds_bucket[5m]))", "legendFormat": "P95"},
          {"expr": "histogram_quantile(0.99, rate(vllm_request_duration_seconds_bucket[5m]))", "legendFormat": "P99"}
        ]
      },
      {
        "title": "Apple Silicon Utilization",
        "type": "gauge",
        "targets": [{
          "expr": "rate(vllm_apple_silicon_requests_total[5m]) / rate(vllm_requests_total[5m]) * 100",
          "legendFormat": "Apple Silicon %"
        }]
      }
    ]
  }
}
```

### 2. AlertManager Configuration

**Alert Routing**
```yaml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@threads-agent-stack.com'
  
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
  # Critical alerts to PagerDuty
  - match:
      severity: critical
    receiver: 'pagerduty'
    
  # Warning alerts to Slack
  - match:
      severity: warning
    receiver: 'slack'
    
  # Info alerts to email
  - match:
      severity: info
    receiver: 'email'

receivers:
- name: 'default'
  email_configs:
  - to: 'team@threads-agent-stack.com'
    subject: 'vLLM Alert: {{ .GroupLabels.alertname }}'
    body: |
      {{ range .Alerts }}
      Alert: {{ .Annotations.summary }}
      Description: {{ .Annotations.description }}
      {{ end }}

- name: 'pagerduty'
  pagerduty_configs:
  - routing_key: '<pagerduty-key>'
    description: 'vLLM Service Critical Alert'
    
- name: 'slack'
  slack_configs:
  - api_url: '<slack-webhook-url>'
    channel: '#vllm-alerts'
    title: 'vLLM Service Alert'
    text: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
    
- name: 'email'
  email_configs:
  - to: 'team@threads-agent-stack.com'
    subject: 'vLLM Info: {{ .GroupLabels.alertname }}'
```

---

## Disaster Recovery and Business Continuity

### 1. Backup Strategy

**Model Cache Backup**
```bash
#!/bin/bash
# backup-model-cache.sh

NAMESPACE="vllm-service"
BACKUP_LOCATION="s3://threads-agent-backups/vllm-models"
DATE=$(date +%Y%m%d_%H%M%S)

echo "Starting model cache backup at $DATE"

# Create persistent volume snapshot
kubectl create -n $NAMESPACE -f - <<EOF
apiVersion: snapshot.storage.k8s.io/v1
kind: VolumeSnapshot
metadata:
  name: vllm-model-cache-snapshot-$DATE
spec:
  source:
    persistentVolumeClaimName: vllm-service-pvc
  volumeSnapshotClassName: fast-ssd-snapclass
EOF

# Wait for snapshot completion
kubectl wait --for=condition=ReadyToUse volumesnapshot/vllm-model-cache-snapshot-$DATE -n $NAMESPACE --timeout=300s

# Copy snapshot to S3 (if using external backup)
kubectl get volumesnapshot vllm-model-cache-snapshot-$DATE -n $NAMESPACE -o yaml > backup-$DATE.yaml
aws s3 cp backup-$DATE.yaml $BACKUP_LOCATION/snapshots/

echo "Model cache backup completed: $DATE"
```

**Configuration Backup**
```bash
#!/bin/bash
# backup-configurations.sh

NAMESPACE="vllm-service"
BACKUP_DIR="/backups/vllm-$(date +%Y%m%d)"

mkdir -p $BACKUP_DIR

# Backup all vLLM service configurations
kubectl get all -n $NAMESPACE -o yaml > $BACKUP_DIR/resources.yaml
kubectl get configmaps -n $NAMESPACE -o yaml > $BACKUP_DIR/configmaps.yaml  
kubectl get secrets -n $NAMESPACE -o yaml > $BACKUP_DIR/secrets.yaml
kubectl get pvc -n $NAMESPACE -o yaml > $BACKUP_DIR/pvc.yaml

# Backup monitoring configurations
kubectl get servicemonitor -n monitoring -l app=vllm-service -o yaml > $BACKUP_DIR/servicemonitor.yaml
kubectl get prometheusrule -n monitoring -l app=vllm-service -o yaml > $BACKUP_DIR/prometheusrule.yaml

# Upload to S3
tar -czf $BACKUP_DIR.tar.gz -C /backups vllm-$(date +%Y%m%d)
aws s3 cp $BACKUP_DIR.tar.gz s3://threads-agent-backups/configurations/

echo "Configuration backup completed"
```

### 2. Disaster Recovery Procedures

**RTO/RPO Targets**
```
Recovery Time Objective (RTO): 15 minutes
Recovery Point Objective (RPO): 5 minutes
Service Level Agreement: 99.9% uptime
```

**Multi-Region Failover Strategy**
```yaml
# disaster-recovery-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: disaster-recovery-config
  namespace: vllm-service
data:
  dr-strategy.yaml: |
    primary_region: "us-west-2"
    dr_region: "us-east-1"
    
    failover_triggers:
      - regional_outage
      - service_degradation > 5min
      - latency_sli_breach > 10min
      
    recovery_procedures:
      1. Validate DR region readiness
      2. Update DNS to DR endpoint  
      3. Scale up DR deployment
      4. Verify service health
      5. Update monitoring dashboards
      
    rollback_procedures:
      1. Verify primary region recovery
      2. Scale up primary deployment
      3. Update DNS back to primary
      4. Scale down DR deployment
      5. Validate full service restoration
```

**Automated DR Testing**
```bash
#!/bin/bash
# dr-test.sh - Monthly DR testing

echo "Starting Disaster Recovery Test"

# 1. Backup current state
kubectl create -n vllm-service configmap dr-test-backup \
  --from-literal=test-date="$(date)" \
  --from-literal=primary-replicas="$(kubectl get deployment vllm-service -n vllm-service -o jsonpath='{.spec.replicas}')"

# 2. Simulate primary region failure
kubectl patch deployment vllm-service -n vllm-service -p '{"spec":{"replicas":0}}'

# 3. Activate DR region
kubectl apply -f disaster-recovery/dr-deployment.yaml

# 4. Validate DR services
sleep 30
DR_HEALTH=$(curl -s http://dr.threads-agent-stack.com/health | jq -r '.status')

if [ "$DR_HEALTH" = "healthy" ]; then
    echo "✅ DR test successful - service healthy in DR region"
else
    echo "❌ DR test failed - service unhealthy in DR region"
fi

# 5. Restore primary
kubectl patch deployment vllm-service -n vllm-service -p '{"spec":{"replicas":3}}'
kubectl delete -f disaster-recovery/dr-deployment.yaml

# 6. Cleanup
kubectl delete configmap dr-test-backup -n vllm-service

echo "DR test completed"
```

---

## Cost Optimization

### 1. Resource Right-sizing

**Cluster Autoscaler Configuration**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-status
  namespace: kube-system
data:
  nodes.max: "10"
  nodes.min: "3"
  scale-down-delay-after-add: "10m"
  scale-down-unneeded-time: "10m"
  skip-nodes-with-local-storage: "false"
  
  # Apple Silicon node pool configuration
  node-group-auto-discovery: "asg:tag=k8s.io/cluster-autoscaler/enabled,k8s.io/cluster-autoscaler/vllm-cluster"
  
  # Cost optimization preferences
  expander: "priority,least-waste"
  balance-similar-node-groups: "true"
  skip-nodes-with-system-pods: "false"
```

**Resource Optimization Policy**
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: vllm-resource-policy
  namespace: vllm-service
data:
  optimization-rules.yaml: |
    # Apple Silicon optimization rules
    apple_silicon:
      preferred: true
      node_selector: "node.threads-agent.com/apple-silicon=true"
      resource_multiplier: 0.8  # 20% more efficient
      
    # Resource scaling policies
    scaling:
      cpu:
        min: "1000m"
        max: "4000m"
        target_utilization: 70
      memory:
        min: "4Gi"
        max: "16Gi"  
        target_utilization: 80
        
    # Cost optimization thresholds
    cost_controls:
      max_monthly_spend: 5000  # USD
      scale_down_threshold: 30  # % utilization
      scale_up_threshold: 80    # % utilization
```

### 2. Intelligent Scaling Policies

**Predictive Auto-scaling**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: vllm-predictive-hpa
  namespace: vllm-service
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: vllm-service
  minReplicas: 2
  maxReplicas: 8
  
  # Cost-aware scaling behavior
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 120  # Slower scale-up to save cost
      policies:
      - type: Percent
        value: 25  # Conservative scaling
        periodSeconds: 60
        
    scaleDown:
      stabilizationWindowSeconds: 600  # Aggressive scale-down for cost
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
        
  metrics:
  # Business hours vs off-hours scaling
  - type: External
    external:
      metric:
        name: business-hours-multiplier
      target:
        type: AverageValue
        averageValue: "1.0"
        
  # Cost per request optimization
  - type: External
    external:
      metric:
        name: cost-per-request-target
      target:
        type: AverageValue
        averageValue: "0.001"  # $0.001 per request
```

---

## Troubleshooting Guide

### Common Issues and Solutions

**1. Apple Silicon Optimization Not Working**
```bash
# Diagnose Apple Silicon issues
kubectl describe node <node-name> | grep -A 10 "Labels"
kubectl get pods -n vllm-service -o wide

# Check MPS availability
kubectl exec -it <pod-name> -n vllm-service -- python -c "
import torch
print(f'MPS Available: {torch.backends.mps.is_available()}')
print(f'MPS Built: {torch.backends.mps.is_built()}')
"

# Solution: Verify node labels and container capabilities
kubectl label nodes <node-name> node.threads-agent.com/apple-silicon=true --overwrite
kubectl patch deployment vllm-service -n vllm-service -p '{"spec":{"template":{"spec":{"nodeSelector":{"node.threads-agent.com/apple-silicon":"true"}}}}}'
```

**2. Latency Target Not Met**
```bash
# Check performance metrics
kubectl port-forward -n vllm-service svc/vllm-service 8090:8090 &
curl http://localhost:8090/performance/latency

# Analyze bottlenecks
kubectl top pods -n vllm-service
kubectl describe hpa vllm-service-hpa -n vllm-service

# Solution: Check resource allocation and scaling
kubectl patch hpa vllm-service-hpa -n vllm-service -p '{"spec":{"maxReplicas":8}}'
```

**3. Circuit Breaker Issues**
```bash
# Check circuit breaker status
curl http://localhost:8090/health | jq '.circuit_breaker_status'

# Reset circuit breaker
kubectl exec -it <pod-name> -n vllm-service -- curl -X POST http://localhost:8090/circuit-breaker/reset

# Solution: Investigate underlying issues
kubectl logs -n vllm-service -l app=vllm-service --tail=100
```

**4. Cost Savings Not Achieved**
```bash
# Validate cost tracking
curl http://localhost:8090/cost-comparison | jq '.summary'

# Check for OpenAI fallback usage
kubectl logs -n vllm-service -l app=vllm-service | grep "fallback"

# Solution: Ensure local inference is working
kubectl exec -it <pod-name> -n vllm-service -- curl -X POST http://localhost:8090/v1/chat/completions -d '{"model":"llama-3-8b","messages":[{"role":"user","content":"test"}]}'
```

---

This comprehensive deployment guide demonstrates enterprise-grade Kubernetes deployment expertise with Apple Silicon optimization, advanced monitoring, cost optimization, and disaster recovery planning suitable for senior infrastructure and GenAI engineering roles.

**Portfolio Value**: Complete production deployment solution showcasing Kubernetes expertise, Apple Silicon specialization, cost engineering, and enterprise operations capabilities that directly translate to infrastructure leadership roles.