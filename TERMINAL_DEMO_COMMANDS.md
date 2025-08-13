# 🖥️ Terminal Demo Commands - Step by Step

## 🎯 **How to Record Terminal Demo (15 seconds)**

### **Setup Before Recording:**

1. **Open Terminal** (new window for clean demo)
2. **Navigate to project root:**
   ```bash
   cd /Users/vitaliiserbyn/development/wt-a1-mlops
   ```
3. **Clear terminal:** `clear`

---

## 🚀 **Recording Commands (Exact Sequence)**

### **Command 1: Navigate to Demo Directory**
```bash
cd services/achievement_collector
```
**⏱️ Time:** 2 seconds  
**🗣️ Say:** *"Let me navigate to the MLOps demo directory"*

### **Command 2: Activate Virtual Environment**
```bash
source ../../.venv/bin/activate
```
**⏱️ Time:** 2 seconds  
**🗣️ Say:** *"Activating the Python environment with MLflow dependencies"*

### **Command 3: Run MLOps Demo**
```bash
python -m mlops.demo_script --quick-demo
```
**⏱️ Time:** 8 seconds (including output)  
**🗣️ Say:** *"Now I'll execute the complete MLOps pipeline demonstration"*

### **Command 4: Show Generated Artifacts**
```bash
ls -la demo_output/
```
**⏱️ Time:** 3 seconds  
**🗣️ Say:** *"The demo generated comprehensive portfolio artifacts"*

---

## 📺 **What the Output Will Show:**

### **Expected Terminal Output:**
```
╔══════════════════════════════════════════════════════════════════════════════╗
║                        MLflow Lifecycle Demo                                 ║
║                     Production-Ready MLOps Pipeline                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  🎯 Demonstrates: Train → Evaluate → Promote → Rollback                     ║
║  🚀 Features: Multiple ML algorithms, SLO validation, automated deployment   ║
║  📊 Output: Visual reports, metrics, and portfolio artifacts                ║
║  ⏱️  Duration: ~90 seconds (perfect for 2-minute recording)                  ║
╚══════════════════════════════════════════════════════════════════════════════╝

================================================================================
🔄 STAGE: TRAINING
📝 Training multiple ML models with MLflow tracking
================================================================================

🎯 KEY ACCOMPLISHMENTS:
  • Multi-algorithm model training (RandomForest, XGBoost, LogisticRegression)
  • SLO-compliant models (accuracy > 85%, p95 latency < 500ms) 
  • Automated promotion through dev→staging→production
  • Performance monitoring with automated rollback (<30s SLO)
  • Complete audit trail and artifact management

🎉 Demo completed successfully!
```

### **Key Points to Highlight During Recording:**
1. **Multi-algorithm training** - Point to "RandomForest, XGBoost, LogisticRegression"
2. **SLO compliance** - Point to "p95 latency < 500ms"  
3. **Complete pipeline** - Point to "Train → Evaluate → Promote → Rollback"
4. **Fast execution** - Point to completion time (~0.5 seconds)
5. **Production ready** - Point to "PostgreSQL + Kubernetes"

---

## 🎬 **Recording Tips for Terminal Demo:**

### **Before Recording:**
- **Terminal settings:**
  - Font size: 18-20pt (readable on video)
  - Window size: Full screen or large
  - Theme: Dark with good contrast
- **Clear history:** `clear && history -c`
- **Test commands** once to ensure they work

### **During Recording:**
- **Type slowly** - Show each command clearly
- **Pause briefly** after each command before hitting Enter
- **Let output complete** before moving to next command
- **Point to key sections** of output with cursor or voice

### **Voiceover Timing:**
- **Start speaking** as you begin typing
- **Highlight key terms** like "MLflow", "SLO", "production"
- **Sound enthusiastic** about the technology
- **Pause for effect** when impressive output appears

---

## 🔧 **Troubleshooting If Commands Fail:**

### **If Virtual Environment Fails:**
```bash
# Alternative activation
cd /Users/vitaliiserbyn/development/wt-a1-mlops
source .venv/bin/activate
cd services/achievement_collector
```

### **If Demo Script Fails:**
```bash
# Check dependencies
python --version
pip list | grep mlflow
```

### **If Path Issues:**
```bash
# Show current location
pwd
ls -la mlops/
```

---

## ✅ **Success Verification:**

### **Demo is Working If You See:**
- ✅ **Colorful header** with demo title
- ✅ **4 stages completed**: training, evaluation, promotion, rollback  
- ✅ **Success message**: "Demo completed successfully!"
- ✅ **Execution time** under 1 second
- ✅ **Artifacts generated** in demo_output/

### **Portfolio Value:**
This terminal demo shows:
- **Command-line proficiency**
- **Python/MLflow expertise**  
- **Production pipeline execution**
- **Automated quality validation**
- **Professional development workflow**

---

## 🎯 **Alternative Demo Commands (if needed):**

### **Verbose Mode for Longer Demo:**
```bash
python -m mlops.demo_script --quick-demo --verbose
```

### **Show Detailed Results:**
```bash
cat demo_output/README_DEMO.md
cat demo_output/demo_results_*.json
```

### **Show MLflow Integration:**
```bash
python -c "import mlflow; print(f'MLflow: {mlflow.__version__}'); print(f'URI: {mlflow.get_tracking_uri()}')"
```

**⚡ Ready to record! The terminal demo will take exactly 15 seconds and showcase professional MLOps pipeline execution.**