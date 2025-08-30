#!/bin/bash
# Apple Silicon Local LM Evaluation - Complete Pipeline

set -e

echo "🚀 APPLE SILICON LOCAL LM EVALUATION - COMPLETE PIPELINE"
echo "================================================================"

# Check environment
echo "🔧 Step 1: Preparing evaluation environment..."
python -m evalsuite.cli prepare

echo ""
echo "🧪 Step 2: Running model evaluation (MPS stack)..."
python -m evalsuite.cli run --stack mps --models all --tasks all

echo ""
echo "⚖️  Step 3: Running pairwise judging..."
python -m evalsuite.cli judge --models all --tasks all --seeds 3

echo ""
echo "🏆 Step 4: Calculating Elo rankings with bootstrap CIs..."
python -m evalsuite.cli rank

echo ""
echo "⚡ Step 5: Measuring performance benchmarks..."
python -m evalsuite.cli perf --stack mps

echo ""
echo "💰 Step 6: Generating cost analysis..."
python -m evalsuite.cli cost

echo ""
echo "📊 Step 7: Building comprehensive report..."
python -m evalsuite.cli report

echo ""
echo "🎉 EVALUATION COMPLETE!"
echo "================================================================"

# Get MLflow run URL
if command -v mlflow >/dev/null 2>&1; then
    echo "🔗 MLflow Dashboard: http://localhost:5000"
    echo "📊 Report: evalsuite/report/report.md"
    echo ""
    echo "💡 View results:"
    echo "   mlflow ui --backend-store-uri ./mlruns --port 5000"
else
    echo "📊 Report: evalsuite/report/report.md"
fi

echo "✅ Professional Apple Silicon model evaluation complete!"