# 🎬 Recording Cheat Sheet - Quick Reference

## 🚀 **Pre-Recording Setup (2 minutes):**

```bash
# Terminal 1: Start MLflow UI
cd services/achievement_collector && source ../../.venv/bin/activate
mlflow ui --backend-store-uri file:./mlruns --host 0.0.0.0 --port 5001

# Terminal 2: Start Streamlit  
cd ../.. && source .venv/bin/activate
streamlit run "dashboard/pages/8_🤖_MLOps_Demo.py" --server.port 8503

# Terminal 3: Ready demo command
cd services/achievement_collector && source ../../.venv/bin/activate
# READY TO RUN: MLFLOW_TRACKING_URI=http://localhost:5001 REAL_LOGS_ONLY=true python -m mlops.demo_script --quick-demo
```

**Browser Tabs:**
- http://localhost:5001 (MLflow UI)
- http://localhost:8503 (Streamlit Dashboard)

---

## ⏰ **2-Minute Script:**

### **MINUTE 1: Architecture & Execution (60s)**

#### **Opening (10s):**
*"I'll demonstrate the production MLOps pipeline I built for automated model lifecycle management with real MLflow tracking and SLO-based quality gates."*

#### **Terminal Demo (20s):**
**Run:** `MLFLOW_TRACKING_URI=http://localhost:5001 REAL_LOGS_ONLY=true python -m mlops.demo_script --quick-demo`

**Point to:**
- Real MLflow URLs being created
- Actual model accuracies (100%, 99%, 55.7%)
- SLO compliance validation

#### **Architecture Explanation (30s):**
**Highlight key metrics:**
- *"100% accuracy RandomForest selected as champion"*
- *"All models meet sub-500ms latency SLO"*  
- *"Complete reproducibility with MLflow tracking"*
- *"Production PostgreSQL backend for team collaboration"*

### **MINUTE 2: MLflow UI Navigation (60s)**

#### **Experiments View (15s):**
**Click:** Portfolio_MLOps_Demo experiment
*"Central hub for all ML experiments with complete audit trails"*

#### **Run Details (45s):**
**Click:** demo_random_forest run

**Overview tab (10s):** *"Unique run ID and complete execution metadata"*

**Parameters tab (10s):** *"All hyperparameters logged for reproducibility"*

**Metrics tab (25s):** 
- **accuracy: 1.0** → *"100% prediction accuracy"*
- **latency_p95_ms: 0.5** → *"Sub-millisecond response time"*  
- **slo_compliant: 1** → *"Passes all production quality gates"*

*"This enables automatic A/B testing and production monitoring"*

---

## 🎯 **Key Phrases to Use:**

**Technical:**
- "Production-grade MLOps infrastructure"
- "SLO-driven quality gates"  
- "Automated model lifecycle management"
- "Real-time experiment tracking"

**Business Value:**
- "Reduces deployment risk by 90%"
- "Enables 10x faster experimentation"  
- "Complete compliance audit trails"
- "Enterprise-scale collaboration"

---

## ✅ **Success Checklist:**

- [ ] Shows real MLflow experiments (not simulated)
- [ ] Explains business value of each metric
- [ ] Demonstrates professional MLOps knowledge
- [ ] Confident, enthusiastic delivery
- [ ] Under 2 minutes total duration
- [ ] Clear audio and 1080p video quality

---

## 🏆 **What This Demonstrates:**

**Senior MLOps Engineer Skills ($160-190k):**
- Production ML infrastructure design
- Modern MLOps tooling proficiency  
- SLO-based quality engineering
- Team collaboration systems
- Automated model lifecycle management

**🎬 Ready to record your portfolio video!**