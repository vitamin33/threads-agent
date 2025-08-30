#!/bin/bash
# Smoke Test - Modern Models Evaluation Pipeline
# Tests modern 7B instruction models on LinkedIn content generation
set -e

echo "🚀 MODERN MODELS SMOKE TEST - LINKEDIN EVALUATION"
echo "=================================================="
echo ""

# Step 1: Prepare environment
echo "📋 Step 1: Preparing evaluation environment..."
python -m evalsuite.cli prepare

echo ""
echo "🏃‍♂️ Step 2: Running model evaluations..."
echo ""

# Step 2: Run evaluations on both stacks
echo "   🔬 Testing MLX stack..."
python -m evalsuite.cli run --stack mlx --models modern --tasks linkedin_smoke

echo ""
echo "   🔬 Testing llama.cpp stack..."  
python -m evalsuite.cli run --stack llamacpp --models modern --tasks linkedin_smoke

echo ""
echo "⚖️  Step 3: Running pairwise judging..."
python -m evalsuite.cli judge --models modern --tasks linkedin_smoke --seeds 3 --allow_ties

echo ""
echo "🏆 Step 4: Calculating Elo rankings with bootstrap CIs..."
python -m evalsuite.cli rank --out report/leaderboard.json

echo ""
echo "⚡ Step 5: Performance benchmarking..."
echo "   📊 MLX performance..."
python -m evalsuite.cli perf --stack mlx

echo "   📊 llama.cpp performance..."
python -m evalsuite.cli perf --stack llamacpp

echo ""
echo "💰 Step 6: Cost analysis..."
python -m evalsuite.cli cost

echo ""
echo "📄 Step 7: Generating final report..."
python -m evalsuite.cli report

echo ""
echo "✅ SMOKE TEST COMPLETE!"
echo ""
echo "📊 Results:"
echo "   • Leaderboard: report/leaderboard.json"
echo "   • Full Report: report/report.md"
echo "   • MLflow UI: mlflow ui --backend-store-uri file:./mlruns"
echo ""
echo "🎯 Modern models evaluated:"
echo "   • Qwen 2.5 7B Instruct"
echo "   • Mistral 7B Instruct v0.3"  
echo "   • Phi-3.5 Mini Instruct"
echo "   • OLMo 7B Instruct"
echo "   • Yi-1.5 6B Chat"
echo "   • OPT-2.7B (legacy baseline)"