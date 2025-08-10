#!/bin/bash

# Simple test script for ML Autoscaling with KEDA

echo "🚀 ML Autoscaling Test"
echo "====================="

# Function to check scaling
check_scaling() {
    echo -e "\n📊 Current Scaling Status:"
    echo "Deployments:"
    kubectl get deployment celery-worker orchestrator -o wide
    echo -e "\nHPA Status:"
    kubectl get hpa | grep -E "(celery|orchestrator)"
    echo -e "\nScaledObjects:"
    kubectl get scaledobjects
}

# Function to generate load by creating jobs
generate_celery_load() {
    echo -e "\n🔄 Generating Celery queue load..."
    
    # Create a job that generates messages
    cat <<EOF | kubectl apply -f -
apiVersion: batch/v1
kind: Job
metadata:
  name: celery-load-test-$(date +%s)
spec:
  template:
    spec:
      containers:
      - name: load-generator
        image: python:3.9-slim
        command: ["python", "-c"]
        args:
          - |
            import time
            print("Generating load for 60 seconds...")
            for i in range(60):
                print(f"Message {i}")
                time.sleep(1)
      restartPolicy: Never
  backoffLimit: 1
EOF
    
    echo "Load generator job created"
}

# Test 1: Check initial state
echo -e "\n📝 Test 1: Initial State"
echo "------------------------"
check_scaling

# Test 2: Check KEDA is working
echo -e "\n📝 Test 2: KEDA Status"
echo "----------------------"
kubectl get pods -n keda
echo -e "\nKEDA Operator logs (last 5 lines):"
kubectl logs -n keda -l app=keda-operator --tail=5 2>/dev/null || echo "Could not fetch logs"

# Test 3: Generate some load
echo -e "\n📝 Test 3: Generate Load"
echo "------------------------"
generate_celery_load

# Wait and monitor
echo -e "\n⏳ Monitoring scaling for 2 minutes..."
for i in {1..6}; do
    echo -e "\n⏱️  Check $i/6 (after $(($i * 20)) seconds):"
    sleep 20
    kubectl get deployment celery-worker orchestrator --no-headers | while read line; do
        echo "  $line"
    done
done

# Test 4: Final state
echo -e "\n📝 Test 4: Final State"
echo "----------------------"
check_scaling

# Test 5: Check events
echo -e "\n📝 Test 5: Scaling Events"
echo "-------------------------"
kubectl get events --sort-by='.lastTimestamp' | grep -i scale | tail -10

echo -e "\n✅ Test Complete!"
echo "Check detailed status with:"
echo "  kubectl describe scaledobject ml-autoscaling-celery-worker-scaler"
echo "  kubectl describe scaledobject ml-autoscaling-orchestrator-scaler"