#!/usr/bin/env python
"""
Generate RabbitMQ load to test KEDA scaling
"""

import json
import time
from datetime import datetime

# Create load using kubectl exec to send messages
import subprocess

def send_rabbitmq_messages(count=100):
    """Send messages to RabbitMQ using kubectl exec"""
    print(f"📤 Sending {count} messages to RabbitMQ...")
    
    # Python script to run inside a pod
    python_script = f'''
import json
for i in range({count}):
    msg = {{"id": i, "timestamp": "{datetime.now().isoformat()}", "data": "test"}}
    print(json.dumps(msg))
'''
    
    # Use the celery-worker pod to send messages
    cmd = [
        "kubectl", "exec", "-it", "deployment/celery-worker", "--",
        "python", "-c",
        f"import pika; import json; "
        f"connection = pika.BlockingConnection(pika.ConnectionParameters('rabbitmq', 5672, '/', pika.PlainCredentials('user', 'pass'))); "
        f"channel = connection.channel(); "
        f"channel.queue_declare(queue='celery', durable=True); "
        f"for i in range({count}): "
        f"  channel.basic_publish(exchange='', routing_key='celery', body=json.dumps({{'id': i, 'data': 'test'}})); "
        f"print(f'Sent {count} messages'); "
        f"connection.close()"
    ]
    
    try:
        # Simpler approach - create a job that generates messages
        job_yaml = f"""
apiVersion: batch/v1
kind: Job
metadata:
  name: rabbitmq-load-{int(time.time())}
spec:
  template:
    spec:
      containers:
      - name: loader
        image: python:3.9-slim
        command: ["sh", "-c"]
        args:
          - |
            pip install pika --quiet
            python -c "
import pika
import json
import time

print('Connecting to RabbitMQ...')
for attempt in range(5):
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                'rabbitmq.default.svc.cluster.local',
                5672, '/',
                pika.PlainCredentials('user', 'pass')
            )
        )
        break
    except:
        print(f'Attempt {{attempt+1}} failed, retrying...')
        time.sleep(2)

channel = connection.channel()
channel.queue_declare(queue='celery', durable=True)

print('Sending {count} messages...')
for i in range({count}):
    msg = {{'id': i, 'timestamp': str(time.time()), 'data': 'load test'}}
    channel.basic_publish(
        exchange='',
        routing_key='celery',
        body=json.dumps(msg),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    if i % 10 == 0:
        print(f'Sent {{i}}/{count} messages')

print('Done! Sent {count} messages')
connection.close()
            "
      restartPolicy: Never
  backoffLimit: 1
"""
        
        # Apply the job
        with open('/tmp/load-job.yaml', 'w') as f:
            f.write(job_yaml)
        
        result = subprocess.run(
            ["kubectl", "apply", "-f", "/tmp/load-job.yaml"],
            capture_output=True,
            text=True
        )
        print(f"✅ Load generator job created: {result.stdout}")
        
        # Wait for job to complete
        print("⏳ Waiting for job to complete...")
        time.sleep(10)
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_scaling():
    """Check current scaling status"""
    print("\n📊 Current Scaling Status:")
    
    # Check deployments
    result = subprocess.run(
        ["kubectl", "get", "deployment", "celery-worker", "-o", "wide"],
        capture_output=True,
        text=True
    )
    print("Celery Worker:", result.stdout.strip())
    
    # Check HPA
    result = subprocess.run(
        ["kubectl", "get", "hpa", "keda-hpa-ml-autoscaling-celery-worker-scaler"],
        capture_output=True,
        text=True
    )
    print("\nHPA Status:", result.stdout.strip())
    
    # Check queue depth
    print("\n📈 To check RabbitMQ queue depth:")
    print("   kubectl exec -it rabbitmq-0 -- rabbitmqctl list_queues")

if __name__ == "__main__":
    print("🚀 RabbitMQ Load Test for KEDA Scaling")
    print("=" * 50)
    
    # Initial status
    check_scaling()
    
    # Generate load
    print("\n🔄 Generating load...")
    send_rabbitmq_messages(100)
    
    # Monitor scaling
    print("\n⏳ Monitoring scaling (2 minutes)...")
    for i in range(6):
        time.sleep(20)
        print(f"\n⏱️  Check {i+1}/6:")
        result = subprocess.run(
            ["kubectl", "get", "deployment", "celery-worker", "--no-headers"],
            capture_output=True,
            text=True
        )
        print(f"   {result.stdout.strip()}")
    
    # Final status
    print("\n" + "=" * 50)
    check_scaling()
    
    print("\n✅ Test complete!")