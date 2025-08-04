#!/bin/bash
# scripts/secure-runner-setup.sh
# Security hardening script for self-hosted GitHub Actions runners

set -euo pipefail

RUNNER_USER="github-runner"
RUNNER_HOME="/home/$RUNNER_USER"

echo "🔐 Setting up secure self-hosted GitHub Actions runner..."

# 1. Create dedicated user
if ! id "$RUNNER_USER" &>/dev/null; then
    sudo useradd -m -s /bin/bash "$RUNNER_USER"
    echo "✅ Created user: $RUNNER_USER"
fi

# 2. Setup SSH key-based access only
sudo mkdir -p "$RUNNER_HOME/.ssh"
sudo chmod 700 "$RUNNER_HOME/.ssh"
echo "✅ SSH directory configured"

# 3. Configure firewall
sudo ufw --force enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow out 443  # HTTPS
sudo ufw allow out 80   # HTTP
echo "✅ Firewall configured"

# 4. Install fail2ban
if ! command -v fail2ban-client &> /dev/null; then
    sudo apt-get update
    sudo apt-get install -y fail2ban
    
    # Configure fail2ban for SSH
    sudo tee /etc/fail2ban/jail.local > /dev/null <<EOF
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
findtime = 600
EOF
    
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    echo "✅ Fail2ban configured"
fi

# 5. Setup automatic security updates
sudo apt-get install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
echo "✅ Automatic security updates enabled"

# 6. Configure log monitoring
sudo tee /etc/logrotate.d/github-runner > /dev/null <<EOF
$RUNNER_HOME/_diag/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
echo "✅ Log rotation configured"

# 7. Setup resource limits
sudo tee /etc/security/limits.d/github-runner.conf > /dev/null <<EOF
$RUNNER_USER soft nproc 32768
$RUNNER_USER hard nproc 65536
$RUNNER_USER soft nofile 65536
$RUNNER_USER hard nofile 65536
$RUNNER_USER soft memlock unlimited
$RUNNER_USER hard memlock unlimited
EOF
echo "✅ Resource limits configured"

# 8. Install Docker with security
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    sudo usermod -aG docker "$RUNNER_USER"
    
    # Configure Docker daemon for security
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "10m",
        "max-file": "3"
    },
    "live-restore": true,
    "userland-proxy": false,
    "no-new-privileges": true,
    "seccomp-profile": "/etc/docker/seccomp.json"
}
EOF
    
    sudo systemctl restart docker
    echo "✅ Docker installed and secured"
fi

# 9. Setup monitoring
sudo tee /usr/local/bin/runner-health-check.sh > /dev/null <<'EOF'
#!/bin/bash
# Health check script for GitHub Actions runner

RUNNER_DIR="/home/github-runner/actions-runner"
LOG_FILE="/var/log/runner-health.log"

# Check if runner service is running
if ! systemctl is-active --quiet actions.runner.* ; then
    echo "$(date): ERROR - Runner service is not active" >> "$LOG_FILE"
    # Send alert (configure with your monitoring system)
    exit 1
fi

# Check disk space
DISK_USAGE=$(df /home | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 90 ]; then
    echo "$(date): WARNING - Disk usage is ${DISK_USAGE}%" >> "$LOG_FILE"
fi

# Check memory usage
MEM_USAGE=$(free | grep Mem | awk '{printf("%.0f", $3/$2 * 100.0)}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "$(date): WARNING - Memory usage is ${MEM_USAGE}%" >> "$LOG_FILE"
fi

# Cleanup old Docker images
docker system prune -f --volumes --filter "until=24h" 2>/dev/null || true

echo "$(date): INFO - Health check completed" >> "$LOG_FILE"
EOF

sudo chmod +x /usr/local/bin/runner-health-check.sh

# Add to crontab
(sudo crontab -l 2>/dev/null; echo "*/10 * * * * /usr/local/bin/runner-health-check.sh") | sudo crontab -
echo "✅ Health monitoring configured"

# 10. Final security checklist
echo ""
echo "🔐 Security Setup Complete!"
echo ""
echo "Next steps:"
echo "1. Configure SSH key authentication"
echo "2. Disable password authentication"
echo "3. Install and configure the GitHub Actions runner as user '$RUNNER_USER'"
echo "4. Setup monitoring alerts"
echo "5. Regular security updates schedule"
echo ""
echo "Runner directory: $RUNNER_HOME/actions-runner"
echo "Health check logs: /var/log/runner-health.log"