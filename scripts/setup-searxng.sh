#!/bin/bash
# Setup SearXNG for Threads-Agent

echo "🔍 Setting up SearXNG for competitive analysis..."

# Create directory for SearXNG config
mkdir -p .searxng

# Create SearXNG settings file
cat > .searxng/settings.yml << 'EOF'
# SearXNG Settings for Threads-Agent
general:
  instance_name: "Threads-Agent Search"
  contact_url: false
  enable_metrics: true

search:
  safe_search: 0
  autocomplete: "duckduckgo"
  default_lang: "en"
  formats:
    - html
    - json

server:
  secret_key: "threads-agent-secret-key-2025"
  bind_address: "0.0.0.0"
  port: 8888
  limiter: false  # Disable rate limiting for local use

engines:
  - name: duckduckgo
    engine: duckduckgo
    shortcut: ddg
    disabled: false
    
  - name: qwant
    engine: qwant
    shortcut: qw
    disabled: false
    categories: [general, web]
    
  - name: google
    engine: google
    shortcut: go
    disabled: false
    
  - name: bing
    engine: bing
    shortcut: bi
    disabled: false
    
  - name: startpage
    engine: startpage
    shortcut: sp
    disabled: false

ui:
  static_use_hash: true
  infinite_scroll: true
  default_theme: simple
  theme_args:
    simple_style: dark

enabled_plugins:
  - 'Hash plugin'
  - 'Search on category select'
  - 'Self Information'
  - 'Tracker URL remover'
EOF

# Create docker-compose file for SearXNG
cat > .searxng/docker-compose.yml << 'EOF'
version: '3.7'

services:
  searxng:
    image: searxng/searxng:latest
    container_name: threads-agent-searxng
    restart: unless-stopped
    ports:
      - "8888:8080"
    volumes:
      - ./settings.yml:/etc/searxng/settings.yml:ro
    environment:
      - SEARXNG_BASE_URL=http://localhost:8888/
      - SEARXNG_SECRET_KEY=threads-agent-secret-key-2025
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    logging:
      driver: "json-file"
      options:
        max-size: "1m"
        max-file: "1"
EOF

echo "✅ SearXNG configuration created"
echo ""
echo "To start SearXNG:"
echo "  cd .searxng && docker-compose up -d"
echo ""
echo "SearXNG will be available at: http://localhost:8888"
echo "API endpoint: http://localhost:8888/search?q=YOUR_QUERY&format=json"
echo ""
echo "To use with MCP:"
echo "  The mcp-searxng server is installed globally"
echo "  Configure it in Claude settings with the local SearXNG URL"