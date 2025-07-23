#!/bin/bash

# Auto-Metrics Dashboard for AI-Powered Development System
# Provides real-time insights into epic progress, velocity, and team performance

set -euo pipefail

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKFLOW_DIR="$(dirname "$SCRIPT_DIR")/.workflows"
METRICS_DIR="$WORKFLOW_DIR/metrics"
DASHBOARD_DIR="$(dirname "$SCRIPT_DIR")/dashboard"

# Create necessary directories
mkdir -p "$METRICS_DIR" "$DASHBOARD_DIR"

# Functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Calculate epic metrics
calculate_epic_metrics() {
    local epic_file="$1"
    local epic_id=$(basename "$epic_file" .yaml)
    
    # Count tasks
    local total_tasks=0
    local completed_tasks=0
    local in_progress_tasks=0
    local blocked_tasks=0
    
    # Find all tasks for this epic
    for task_file in "$WORKFLOW_DIR/tasks"/task_*_*.yaml; do
        if [[ -f "$task_file" ]] && grep -q "epic_id: \"$epic_id\"" "$task_file"; then
            ((total_tasks++))
            
            # Check task status
            if grep -q 'status: "completed"' "$task_file"; then
                ((completed_tasks++))
            elif grep -q 'status: "in_progress"' "$task_file"; then
                ((in_progress_tasks++))
            elif grep -q 'blocked: true' "$task_file" 2>/dev/null; then
                ((blocked_tasks++))
            fi
        fi
    done
    
    # Calculate completion percentage
    local completion_percentage=0
    if [[ $total_tasks -gt 0 ]]; then
        completion_percentage=$((completed_tasks * 100 / total_tasks))
    fi
    
    # Extract epic details
    local epic_name=$(grep '^name:' "$epic_file" | cut -d'"' -f2)
    local created_date=$(grep '^created:' "$epic_file" | cut -d'"' -f2 | cut -d'T' -f1)
    
    # Output JSON
    cat << EOF
{
    "epic_id": "$epic_id",
    "name": "$epic_name",
    "total_tasks": $total_tasks,
    "completed_tasks": $completed_tasks,
    "in_progress_tasks": $in_progress_tasks,
    "blocked_tasks": $blocked_tasks,
    "completion_percentage": $completion_percentage,
    "created_date": "$created_date"
}
EOF
}

# Calculate team metrics
calculate_team_metrics() {
    local team_metrics='{"team_members": ['
    local first=true
    
    # Track unique assignees and their task counts
    declare -A assignee_tasks
    declare -A assignee_completed
    declare -A assignee_in_progress
    
    for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
        if [[ -f "$task_file" ]]; then
            local assignee=$(grep '^assigned_to:' "$task_file" 2>/dev/null | cut -d'"' -f2 || echo "unassigned")
            local status=$(grep '^status:' "$task_file" | cut -d'"' -f2)
            
            # Initialize counters
            [[ -z "${assignee_tasks[$assignee]:-}" ]] && assignee_tasks[$assignee]=0
            [[ -z "${assignee_completed[$assignee]:-}" ]] && assignee_completed[$assignee]=0
            [[ -z "${assignee_in_progress[$assignee]:-}" ]] && assignee_in_progress[$assignee]=0
            
            ((assignee_tasks[$assignee]++))
            
            if [[ "$status" == "completed" ]]; then
                ((assignee_completed[$assignee]++))
            elif [[ "$status" == "in_progress" ]]; then
                ((assignee_in_progress[$assignee]++))
            fi
        fi
    done
    
    # Build JSON
    for assignee in "${!assignee_tasks[@]}"; do
        [[ "$first" == "false" ]] && team_metrics+=","
        team_metrics+="
        {
            \"name\": \"$assignee\",
            \"total_tasks\": ${assignee_tasks[$assignee]},
            \"completed_tasks\": ${assignee_completed[$assignee]:-0},
            \"in_progress_tasks\": ${assignee_in_progress[$assignee]:-0}
        }"
        first=false
    done
    
    team_metrics+=']}'
    echo "$team_metrics"
}

# Calculate velocity metrics
calculate_velocity_metrics() {
    # Calculate tasks completed per day for the last 7 days
    local velocity_data='{"daily_velocity": ['
    local first=true
    
    for i in {6..0}; do
        local date=$(date -v-${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days ago" +%Y-%m-%d)
        local completed_count=0
        
        # Count tasks completed on this date
        for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
            if [[ -f "$task_file" ]] && grep -q 'status: "completed"' "$task_file"; then
                # Check if completed date matches (approximation based on updated field)
                if grep -q "updated: \"$date" "$task_file" 2>/dev/null; then
                    ((completed_count++))
                fi
            fi
        done
        
        [[ "$first" == "false" ]] && velocity_data+=","
        velocity_data+="
        {
            \"date\": \"$date\",
            \"completed_tasks\": $completed_count
        }"
        first=false
    done
    
    velocity_data+='],'
    
    # Add weekly average
    local total_completed=0
    for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
        if [[ -f "$task_file" ]] && grep -q 'status: "completed"' "$task_file"; then
            ((total_completed++))
        fi
    done
    
    local avg_velocity=$(echo "scale=1; $total_completed / 7" | bc -l 2>/dev/null || echo 0)
    velocity_data+="\"average_velocity\": $avg_velocity,"
    
    # Add burndown data
    velocity_data+='"burndown_data": ['
    first=true
    local remaining_tasks=0
    
    for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
        if [[ -f "$task_file" ]] && ! grep -q 'status: "completed"' "$task_file"; then
            ((remaining_tasks++))
        fi
    done
    
    for i in {0..6}; do
        local future_date=$(date -v+${i}d +%Y-%m-%d 2>/dev/null || date -d "$i days" +%Y-%m-%d)
        local projected_remaining=$((remaining_tasks - (i * ${avg_velocity%.*})))
        [[ $projected_remaining -lt 0 ]] && projected_remaining=0
        
        [[ "$first" == "false" ]] && velocity_data+=","
        velocity_data+="
        {
            \"date\": \"$future_date\",
            \"remaining_tasks\": $projected_remaining
        }"
        first=false
    done
    
    velocity_data+=']}'
    echo "$velocity_data"
}

# Calculate time tracking metrics
calculate_time_metrics() {
    local time_data='{"time_tracking": {'
    
    # Average time per task (based on created/updated timestamps)
    local total_time=0
    local completed_tasks=0
    
    for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
        if [[ -f "$task_file" ]] && grep -q 'status: "completed"' "$task_file"; then
            local created=$(grep '^created:' "$task_file" | cut -d'"' -f2 || echo "")
            local updated=$(grep '^updated:' "$task_file" | cut -d'"' -f2 || echo "")
            
            if [[ -n "$created" ]] && [[ -n "$updated" ]]; then
                # Simple day difference calculation
                ((completed_tasks++))
            fi
        fi
    done
    
    # Task distribution by priority
    local high_priority=0
    local medium_priority=0
    local low_priority=0
    
    for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
        if [[ -f "$task_file" ]]; then
            if grep -q 'priority: "high"' "$task_file"; then
                ((high_priority++))
            elif grep -q 'priority: "medium"' "$task_file"; then
                ((medium_priority++))
            else
                ((low_priority++))
            fi
        fi
    done
    
    time_data+="
        \"priority_distribution\": {
            \"high\": $high_priority,
            \"medium\": $medium_priority,
            \"low\": $low_priority
        },"
    
    # Effort estimation accuracy
    local estimated_total=0
    local actual_total=0
    
    for task_file in "$WORKFLOW_DIR/tasks"/*.yaml; do
        if [[ -f "$task_file" ]]; then
            local estimated=$(grep '^time_estimated:' "$task_file" | awk '{print $2}' || echo 0)
            local actual=$(grep '^time_actual:' "$task_file" | awk '{print $2}' || echo 0)
            estimated_total=$((estimated_total + estimated))
            actual_total=$((actual_total + actual))
        fi
    done
    
    time_data+="
        \"effort_accuracy\": {
            \"total_estimated\": $estimated_total,
            \"total_actual\": $actual_total
        }
    }}"
    
    echo "$time_data"
}

# Generate complete metrics JSON
generate_metrics() {
    local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    
    # Start JSON
    echo "{"
    echo "  \"timestamp\": \"$timestamp\","
    echo "  \"epics\": ["
    
    # Process each epic
    local first_epic=true
    for epic_file in "$WORKFLOW_DIR/epics"/epic_*.yaml; do
        if [[ -f "$epic_file" ]]; then
            [[ "$first_epic" == "false" ]] && echo ","
            echo -n "    "
            calculate_epic_metrics "$epic_file"
            first_epic=false
        fi
    done
    
    echo "  ],"
    
    # Add team metrics
    echo -n "  "
    calculate_team_metrics
    echo ","
    
    # Add velocity metrics  
    echo -n "  "
    calculate_velocity_metrics
    echo ","
    
    # Add time tracking metrics
    echo -n "  "
    calculate_time_metrics
    
    echo "}"
}

# Create HTML dashboard
create_dashboard_html() {
    cat > "$DASHBOARD_DIR/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Development Metrics Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .metric-card h3 {
            margin: 0 0 15px 0;
            color: #333;
        }
        .progress-bar {
            width: 100%;
            height: 30px;
            background: #e0e0e0;
            border-radius: 15px;
            overflow: hidden;
            margin: 10px 0;
        }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50, #8BC34A);
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
        }
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .stats {
            display: flex;
            justify-content: space-around;
            margin: 15px 0;
        }
        .stat {
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            font-size: 0.9em;
        }
        .alert {
            background: #ff5252;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .team-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .team-member {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 AI Development Metrics Dashboard</h1>
        <p>Real-time insights into your AI-powered development workflow</p>
        <div id="last-updated" style="font-size: 0.9em; opacity: 0.8;"></div>
    </div>

    <div class="metrics-grid">
        <div class="metric-card">
            <h3>📊 Overall Progress</h3>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="total-epics">0</div>
                    <div class="stat-label">Active Epics</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="total-tasks">0</div>
                    <div class="stat-label">Total Tasks</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="completion-rate">0%</div>
                    <div class="stat-label">Completion</div>
                </div>
            </div>
        </div>

        <div class="metric-card">
            <h3>🏃 Current Status</h3>
            <div class="stats">
                <div class="stat">
                    <div class="stat-value" id="in-progress-tasks">0</div>
                    <div class="stat-label">In Progress</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="blocked-tasks">0</div>
                    <div class="stat-label">Blocked</div>
                </div>
                <div class="stat">
                    <div class="stat-value" id="pending-tasks">0</div>
                    <div class="stat-label">Pending</div>
                </div>
            </div>
        </div>
    </div>

    <div id="blocked-alerts"></div>

    <div class="chart-container">
        <h3>📈 Epic Progress</h3>
        <div id="epics-container"></div>
    </div>

    <div class="metrics-grid">
        <div class="chart-container">
            <h3>📊 7-Day Velocity</h3>
            <canvas id="velocity-chart"></canvas>
        </div>

        <div class="chart-container">
            <h3>👥 Team Workload</h3>
            <div id="team-container" class="team-grid"></div>
        </div>
    </div>

    <div class="metrics-grid">
        <div class="chart-container">
            <h3>📈 Burndown Chart</h3>
            <canvas id="burndown-chart"></canvas>
        </div>

        <div class="chart-container">
            <h3>🎯 Priority Distribution</h3>
            <canvas id="priority-chart"></canvas>
        </div>
    </div>

    <script>
        let velocityChart = null;
        let burndownChart = null;
        let priorityChart = null;

        async function fetchMetrics() {
            try {
                const response = await fetch('/metrics.json');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Error fetching metrics:', error);
            }
        }

        function updateDashboard(data) {
            // Update timestamp
            document.getElementById('last-updated').textContent = 
                'Last updated: ' + new Date(data.timestamp).toLocaleString();

            // Calculate totals
            let totalTasks = 0;
            let completedTasks = 0;
            let inProgressTasks = 0;
            let blockedTasks = 0;
            let pendingTasks = 0;

            data.epics.forEach(epic => {
                totalTasks += epic.total_tasks;
                completedTasks += epic.completed_tasks;
                inProgressTasks += epic.in_progress_tasks;
                blockedTasks += epic.blocked_tasks;
                pendingTasks += epic.total_tasks - epic.completed_tasks - epic.in_progress_tasks;
            });

            // Update overall metrics
            document.getElementById('total-epics').textContent = data.epics.length;
            document.getElementById('total-tasks').textContent = totalTasks;
            document.getElementById('completion-rate').textContent = 
                totalTasks > 0 ? Math.round(completedTasks / totalTasks * 100) + '%' : '0%';
            
            document.getElementById('in-progress-tasks').textContent = inProgressTasks;
            document.getElementById('blocked-tasks').textContent = blockedTasks;
            document.getElementById('pending-tasks').textContent = pendingTasks;

            // Show blocked alerts
            const alertsContainer = document.getElementById('blocked-alerts');
            alertsContainer.innerHTML = '';
            if (blockedTasks > 0) {
                alertsContainer.innerHTML = `
                    <div class="alert">
                        ⚠️ ${blockedTasks} tasks are currently blocked and need attention!
                    </div>
                `;
            }

            // Update epic progress bars
            const epicsContainer = document.getElementById('epics-container');
            epicsContainer.innerHTML = data.epics.map(epic => `
                <div class="metric-card">
                    <h4>${epic.name}</h4>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${epic.completion_percentage}%">
                            ${epic.completion_percentage}%
                        </div>
                    </div>
                    <div class="stats">
                        <div class="stat">
                            <div class="stat-value">${epic.completed_tasks}/${epic.total_tasks}</div>
                            <div class="stat-label">Tasks</div>
                        </div>
                        <div class="stat">
                            <div class="stat-value">${epic.in_progress_tasks}</div>
                            <div class="stat-label">Active</div>
                        </div>
                        ${epic.blocked_tasks > 0 ? `
                            <div class="stat" style="color: #ff5252;">
                                <div class="stat-value">${epic.blocked_tasks}</div>
                                <div class="stat-label">Blocked</div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `).join('');

            // Update velocity chart
            updateVelocityChart(data.daily_velocity);

            // Update team workload
            const teamContainer = document.getElementById('team-container');
            teamContainer.innerHTML = data.team_members.map(member => `
                <div class="team-member">
                    <h4>${member.name}</h4>
                    <div>Total: ${member.total_tasks}</div>
                    <div>Completed: ${member.completed_tasks}</div>
                    <div>Active: ${member.in_progress_tasks}</div>
                </div>
            `).join('');

            // Update burndown chart
            if (data.burndown_data) {
                updateBurndownChart(data.burndown_data);
            }

            // Update priority chart
            if (data.time_tracking && data.time_tracking.priority_distribution) {
                updatePriorityChart(data.time_tracking.priority_distribution);
            }
        }

        function updateVelocityChart(velocityData) {
            const ctx = document.getElementById('velocity-chart').getContext('2d');
            
            if (velocityChart) {
                velocityChart.destroy();
            }

            velocityChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: velocityData.map(d => new Date(d.date).toLocaleDateString()),
                    datasets: [{
                        label: 'Tasks Completed',
                        data: velocityData.map(d => d.completed_tasks),
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        }

        function updateBurndownChart(burndownData) {
            const ctx = document.getElementById('burndown-chart').getContext('2d');
            
            if (burndownChart) {
                burndownChart.destroy();
            }

            burndownChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: burndownData.map(d => new Date(d.date).toLocaleDateString()),
                    datasets: [{
                        label: 'Projected Remaining Tasks',
                        data: burndownData.map(d => d.remaining_tasks),
                        borderColor: '#ff6384',
                        backgroundColor: 'rgba(255, 99, 132, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        }

        function updatePriorityChart(priorityData) {
            const ctx = document.getElementById('priority-chart').getContext('2d');
            
            if (priorityChart) {
                priorityChart.destroy();
            }

            priorityChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: ['High Priority', 'Medium Priority', 'Low Priority'],
                    datasets: [{
                        data: [priorityData.high, priorityData.medium, priorityData.low],
                        backgroundColor: [
                            '#ff6384',
                            '#ffcd56',
                            '#36a2eb'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }

        // Initial fetch and auto-refresh
        fetchMetrics();
        setInterval(fetchMetrics, 30000); // Refresh every 30 seconds
    </script>
</body>
</html>
EOF
}

# Start simple web server
start_dashboard_server() {
    log_info "Starting dashboard server..."
    
    # Generate initial metrics
    generate_metrics > "$DASHBOARD_DIR/metrics.json"
    
    # Create HTML
    create_dashboard_html
    
    # Create simple Python server
    cat > "$DASHBOARD_DIR/server.py" << 'EOF'
#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import subprocess
from datetime import datetime

PORT = 8888

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics.json':
            # Regenerate metrics on each request
            result = subprocess.run([
                os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'metrics-dashboard.sh'),
                'generate-json'
            ], capture_output=True, text=True)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(result.stdout.encode())
        else:
            super().do_GET()

os.chdir(os.path.dirname(__file__))

with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
    print(f"Dashboard running at http://localhost:{PORT}")
    httpd.serve_forever()
EOF
    
    chmod +x "$DASHBOARD_DIR/server.py"
    
    # Start server in background
    python3 "$DASHBOARD_DIR/server.py" &
    local server_pid=$!
    
    # Wait a moment for server to start
    sleep 2
    
    log_success "Dashboard is running at http://localhost:8888"
    
    # Open in browser
    if command -v open >/dev/null; then
        open "http://localhost:8888"
    elif command -v xdg-open >/dev/null; then
        xdg-open "http://localhost:8888"
    fi
    
    # Keep running
    log_info "Press Ctrl+C to stop the dashboard"
    wait $server_pid
}

# Main logic
case "${1:-}" in
    "generate-json")
        generate_metrics
        ;;
    "start"|"")
        start_dashboard_server
        ;;
    *)
        echo "Usage: $0 [start|generate-json]"
        exit 1
        ;;
esac