#!/bin/bash

echo "🚀 Tech Doc Generator Setup & Run Script"
echo "========================================"

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Run this script from the tech_doc_generator directory"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt -q

# Create sample env if needed
if [ ! -f ".env" ] && [ ! -f ".env.sample" ]; then
    echo "📝 Creating sample .env file..."
    python create_sample_env.py
fi

# Check for API keys
echo ""
echo "🔑 Checking API keys..."

if [ -f ".env" ]; then
    source .env
    
    if [ -n "$OPENAI_API_KEY" ] && [ "$OPENAI_API_KEY" != "your_openai_api_key_here" ]; then
        echo "✅ OpenAI API key found"
    else
        echo "⚠️  OpenAI API key not set (required for content generation)"
    fi
    
    if [ -n "$DEVTO_API_KEY" ]; then
        echo "✅ Dev.to API key found"
    else
        echo "ℹ️  Dev.to API key not set (optional)"
    fi
    
    if [ -n "$THREADS_ACCESS_TOKEN" ]; then
        echo "✅ Threads access token found"
    else
        echo "ℹ️  Threads access token not set (optional)"
    fi
else
    echo "⚠️  No .env file found. Copy .env.sample to .env and add your keys."
fi

echo ""
echo "📋 Available Commands:"
echo "  1. Run tests:           python -m pytest tests/"
echo "  2. Test integration:    python test_integration.py"
echo "  3. Generate article:    python generate_first_article.py"
echo "  4. Test publishing:     python test_real_publishing.py"
echo ""

# Ask what to do
echo "What would you like to do?"
echo "1) Run tests"
echo "2) Generate your first article"
echo "3) Test with mock data"
echo "4) Exit"
echo ""
read -p "Select option (1-4): " choice

case $choice in
    1)
        echo "🧪 Running tests..."
        python -m pytest tests/ -v
        ;;
    2)
        echo "📝 Generating article..."
        python generate_first_article.py
        ;;
    3)
        echo "🎭 Running mock test..."
        python test_simple.py
        ;;
    4)
        echo "👋 Goodbye!"
        ;;
    *)
        echo "Invalid option"
        ;;
esac