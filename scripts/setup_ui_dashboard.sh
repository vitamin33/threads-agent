#!/bin/bash

# Threads-Agent Streamlit Dashboard Setup Script
# Sets up the Streamlit dashboard for local and production use

set -e

echo "🚀 Setting up Threads-Agent Streamlit Dashboard"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed. Please install Python 3.9+ first."
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MINOR" -lt 9 ]; then
        log_error "Python 3.9+ is required. Current version: $(python3 --version)"
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed."
        exit 1
    fi
    
    # Check Docker (optional)
    if command -v docker &> /dev/null; then
        log_success "Docker found - container deployment available"
        DOCKER_AVAILABLE=true
    else
        log_warning "Docker not found - only local development available"
        DOCKER_AVAILABLE=false
    fi
    
    # Check kubectl (optional)
    if command -v kubectl &> /dev/null; then
        log_success "kubectl found - Kubernetes deployment available"
        KUBECTL_AVAILABLE=true
    else
        log_warning "kubectl not found - Kubernetes deployment not available"
        KUBECTL_AVAILABLE=false
    fi
    
    log_success "Prerequisites check completed"
}

# Setup dashboard directory
setup_dashboard_directory() {
    log_info "Setting up dashboard directory..."
    
    cd "$(dirname "$0")/.."
    
    # Check if dashboard directory exists
    if [ ! -d "dashboard" ]; then
        log_error "Dashboard directory not found. Please ensure the dashboard code is in place."
        exit 1
    fi
    
    cd dashboard
    
    log_success "Dashboard directory found"
}

# Setup Python virtual environment
setup_virtual_environment() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    log_success "Virtual environment ready"
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    if [ ! -f "requirements.txt" ]; then
        log_error "requirements.txt not found"
        exit 1
    fi
    
    pip install -r requirements.txt
    
    log_success "Dependencies installed"
}

# Create environment file
create_env_file() {
    log_info "Creating environment configuration..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Threads Agent Dashboard Configuration

# API URLs - Update these for your environment
ACHIEVEMENT_API_URL=http://localhost:8000
TECH_DOC_API_URL=http://localhost:8001
ORCHESTRATOR_URL=http://localhost:8080
VIRAL_ENGINE_URL=http://localhost:8003

# For Kubernetes deployment
# ACHIEVEMENT_API_URL=http://achievement-collector:8000
# TECH_DOC_API_URL=http://tech-doc-generator:8001
# ORCHESTRATOR_URL=http://orchestrator:8080
# VIRAL_ENGINE_URL=http://viral-engine:8003

# Streamlit Configuration
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_ADDRESS=0.0.0.0
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
EOF
        
        log_info "Created .env file - please update API URLs as needed"
    else
        log_info ".env file already exists"
    fi
}

# Create Streamlit config
create_streamlit_config() {
    log_info "Creating Streamlit configuration..."
    
    mkdir -p .streamlit
    
    cat > .streamlit/config.toml << EOF
[theme]
primaryColor = "#2E86AB"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"

[server]
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
EOF
    
    log_success "Streamlit configuration created"
}

# Setup development script
setup_dev_script() {
    log_info "Creating development startup script..."
    
    cat > start-dev.sh << 'EOF'
#!/bin/bash

echo "🚀 Starting Threads-Agent Streamlit Dashboard"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Run setup script first."
    exit 1
fi

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Start Streamlit
echo "✅ Dashboard starting at http://localhost:8501"
echo "📊 Main dashboard: http://localhost:8501"
echo "🔍 Health check: http://localhost:8501/_stcore/health"
echo ""
echo "Press Ctrl+C to stop"

streamlit run app.py
EOF
    
    chmod +x start-dev.sh
    
    log_success "Development script created"
}

# Build Docker image
build_docker_image() {
    if [ "$DOCKER_AVAILABLE" != true ]; then
        log_warning "Skipping Docker build - Docker not available"
        return
    fi
    
    log_info "Building Docker image..."
    
    docker build -t threads-agent/dashboard:latest .
    
    log_success "Docker image built: threads-agent/dashboard:latest"
}

# Setup Docker Compose
setup_docker_compose() {
    if [ "$DOCKER_AVAILABLE" != true ]; then
        log_warning "Skipping Docker Compose setup - Docker not available"
        return
    fi
    
    log_info "Setting up Docker Compose..."
    
    # Check if network exists
    if ! docker network ls | grep -q threads-agent; then
        log_info "Creating Docker network..."
        docker network create threads-agent_default
    fi
    
    log_success "Docker Compose ready"
}

# Setup Kubernetes
setup_kubernetes() {
    if [ "$KUBECTL_AVAILABLE" != true ]; then
        log_warning "Skipping Kubernetes setup - kubectl not available"
        return
    fi
    
    log_info "Setting up Kubernetes resources..."
    
    # Create namespace if it doesn't exist
    kubectl create namespace threads-agent --dry-run=client -o yaml | kubectl apply -f -
    
    # Apply configurations
    if [ -f "k8s/deployment.yaml" ]; then
        log_info "Applying Kubernetes deployment..."
        kubectl apply -f k8s/deployment.yaml
    fi
    
    log_success "Kubernetes setup completed"
}

# Main execution
main() {
    log_info "Starting Threads-Agent Streamlit Dashboard setup..."
    
    check_prerequisites
    setup_dashboard_directory
    setup_virtual_environment
    install_dependencies
    create_env_file
    create_streamlit_config
    setup_dev_script
    build_docker_image
    setup_docker_compose
    setup_kubernetes
    
    # Deactivate virtual environment
    deactivate 2>/dev/null || true
    
    log_success "🎉 Threads-Agent Streamlit Dashboard setup completed!"
    
    echo ""
    echo "📋 Next steps:"
    echo "1. Update API URLs in .env file (if needed)"
    echo "2. Start dashboard: ./start-dev.sh"
    echo "3. Visit dashboard: http://localhost:8501"
    
    if [ "$DOCKER_AVAILABLE" = true ]; then
        echo ""
        echo "🐳 Docker commands:"
        echo "• Run with Docker: docker run -p 8501:8501 threads-agent/dashboard:latest"
        echo "• Run with Compose: docker-compose up"
    fi
    
    if [ "$KUBECTL_AVAILABLE" = true ]; then
        echo ""
        echo "☸️  Kubernetes commands:"
        echo "• Deploy: kubectl apply -f k8s/deployment.yaml"
        echo "• Check status: kubectl get pods -n threads-agent"
        echo "• Port forward: kubectl port-forward -n threads-agent svc/threads-agent-dashboard 8501:80"
    fi
    
    echo ""
    echo "🔗 Useful URLs:"
    echo "• Main Dashboard: http://localhost:8501"
    echo "• Health Check: http://localhost:8501/_stcore/health"
    echo "• Metrics: http://localhost:8501/~/+/metrics"
}

# Run main function
main "$@"