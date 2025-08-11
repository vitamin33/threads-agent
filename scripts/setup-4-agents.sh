#\!/bin/bash
# Production-ready setup for 4 parallel Claude Code agents
set -e

echo "🚀 Setting up 4 Parallel Claude Code Agents"
echo "==========================================="

BASE_DIR="/Users/vitaliiserbyn/development/threads-agent"
cd "$BASE_DIR"

# Clean up existing worktrees
echo "Cleaning up..."
for wt in ../wt-a*; do
  [ -d "$wt" ] && git worktree remove "$wt" --force 2>/dev/null || true
done
git branch -D feat/a1/main feat/a2/main feat/a3/main feat/a4/main 2>/dev/null || true

# Create lock directory
mkdir -p .locks

# Create worktrees
echo "Creating worktrees..."
git worktree add -b feat/a1/main ../wt-a1-mlops main
git worktree add -b feat/a2/main ../wt-a2-genai main  
git worktree add -b feat/a3/main ../wt-a3-analytics main
git worktree add -b feat/a4/main ../wt-a4-platform main

# Configure each worktree
for dir in ../wt-a*; do
  [ \! -d "$dir" ] && continue
  
  # Copy gitignore
  cp .gitignore "$dir/"
  
  # Determine agent ID from directory name
  case "$(basename $dir)" in
    wt-a1-mlops) agent_id="a1"; port=0; services="orchestrator,celery_worker,persona_runtime" ;;
    wt-a2-genai) agent_id="a2"; port=100; services="viral_engine,rag_pipeline,vllm_service" ;;
    wt-a3-analytics) agent_id="a3"; port=200; services="achievement_collector,dashboard_api,finops_engine" ;;
    wt-a4-platform) agent_id="a4"; port=300; services="revenue,event_bus,threads_adaptor" ;;
  esac
  
  # Create .agent.env
  echo "AGENT_ID=$agent_id" > "$dir/.agent.env"
  echo "PORT_OFFSET=$port" >> "$dir/.agent.env"
  echo "DB_SCHEMA=agent_$agent_id" >> "$dir/.agent.env"
  echo "AGENT_SERVICES=\"$services\"" >> "$dir/.agent.env"
  
  # Create AGENT_FOCUS.md
  echo "# Agent $agent_id" > "$dir/AGENT_FOCUS.md"
  echo "Services: $services" >> "$dir/AGENT_FOCUS.md"
  echo "Ports: $((8080+port))-$((8099+port))" >> "$dir/AGENT_FOCUS.md"
  
  # Create Python venv
  (cd "$dir" && python3 -m venv .venv 2>/dev/null || true)
  
  echo "✓ Configured $(basename $dir)"
done

echo ""
echo "✅ Setup Complete\!"
echo ""
echo "Worktrees created:"
echo "  ../wt-a1-mlops     → Orchestrator, Celery, Persona"
echo "  ../wt-a2-genai     → Viral Engines, RAG, vLLM"
echo "  ../wt-a3-analytics → Achievements, Dashboard, FinOps"
echo "  ../wt-a4-platform  → Revenue, Events, Threads Adaptor"
echo ""
echo "Next: Open 4 editor windows, one for each worktree"
