#!/bin/bash
# Setup persistent achievement storage

echo "🚀 Achievement Collector - Persistent Storage Setup"
echo "=================================================="

# Option 1: Local PostgreSQL
setup_local_postgres() {
    echo "Setting up local PostgreSQL..."
    
    # Check if PostgreSQL is installed
    if ! command -v psql &> /dev/null; then
        echo "Installing PostgreSQL..."
        brew install postgresql@16
        brew services start postgresql@16
    fi
    
    # Create database
    createdb achievements_dev 2>/dev/null || echo "Database already exists"
    
    # Create .env file
    cat > services/achievement_collector/.env.local << EOF
DATABASE_URL=postgresql://localhost/achievements_dev
OPENAI_API_KEY=${OPENAI_API_KEY:-your-api-key}
GITHUB_WEBHOOK_SECRET=your-webhook-secret
EOF
    
    echo "✅ Local PostgreSQL ready at: postgresql://localhost/achievements_dev"
}

# Option 2: Docker PostgreSQL
setup_docker_postgres() {
    echo "Setting up Docker PostgreSQL..."
    
    # Create volume
    docker volume create achievements_data
    
    # Run PostgreSQL
    docker run -d \
        --name achievements-db \
        -e POSTGRES_DB=achievements \
        -e POSTGRES_PASSWORD=achievements123 \
        -v achievements_data:/var/lib/postgresql/data \
        -p 5433:5432 \
        postgres:16
    
    # Wait for PostgreSQL to start
    sleep 5
    
    echo "✅ Docker PostgreSQL ready at: postgresql://postgres:achievements123@localhost:5433/achievements"
}

# Option 3: Backup current k3d data
backup_k3d_data() {
    echo "Backing up current k3d PostgreSQL data..."
    
    # Create backup directory
    mkdir -p backups/achievements
    
    # Dump database
    kubectl exec -it postgres-0 -- pg_dump -U postgres threads > backups/achievements/backup_$(date +%Y%m%d_%H%M%S).sql
    
    echo "✅ Backup saved to: backups/achievements/"
}

# Option 4: Setup Supabase (free cloud)
setup_supabase() {
    echo "Setting up Supabase..."
    echo "1. Go to https://supabase.com and create a free account"
    echo "2. Create a new project"
    echo "3. Copy the connection string from Settings > Database"
    echo "4. Update DATABASE_URL in your .env file"
    echo ""
    echo "Example connection string:"
    echo "postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres"
}

# Menu
echo "Choose storage option:"
echo "1) Local PostgreSQL (recommended for dev)"
echo "2) Docker PostgreSQL with persistent volume"
echo "3) Backup current k3d data"
echo "4) Setup free cloud database (Supabase)"
echo "5) All of the above"

read -p "Enter choice [1-5]: " choice

case $choice in
    1) setup_local_postgres ;;
    2) setup_docker_postgres ;;
    3) backup_k3d_data ;;
    4) setup_supabase ;;
    5) 
        backup_k3d_data
        setup_local_postgres
        setup_docker_postgres
        setup_supabase
        ;;
    *) echo "Invalid choice" ;;
esac

echo ""
echo "Next steps:"
echo "1. Run migrations: cd services/achievement_collector && alembic upgrade head"
echo "2. Start service: uvicorn main:app --reload"
echo "3. Store achievements: ./scripts/store-ci-achievement.sh"