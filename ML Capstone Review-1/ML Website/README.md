# End-to-End ML Pipeline for Predictive Maintenance of Industrial Pumps & Compressors (Fluid Dynamics)

A complete, modern, professional web application designed for a B.Tech CSE Capstone Project. The system integrates fluid dynamics analysis (pump head, pressure differential, vibration RMS, flow turbulence) with machine learning pipelines (Decision Trees, Random Forest, XGBoost) to perform early failure prediction and prescriptive maintenance alerts for industrial pumps and compressors.

---

## 🌟 Key Features & Capstone Architecture

The application is engineered into **two main modules** with supporting dashboard and dataset management features:

### **Module 1: Fluid Dynamics Data Acquisition & Analysis**
- **CSV Telemetry Upload & Validation**: Secure CSV ingestion, schema validation, and upload tracking.
- **Sensor Parameters Supported**: Timestamp, Pressure, Flow Rate, Temperature, Vibration RMS, RPM, Motor Current, Pump Head, Operating Hours, Failure Status.
- **Data Preprocessing Engine**:
  - Missing value detection & mean/median imputation.
  - Duplicate record identification & removal.
  - IQR (1.5x) and Z-score outlier detection and capping.
  - Rolling mean noise reduction filter.
  - MinMax & StandardScaler normalization.
- **Fluid Dynamics Calculations**: Pressure delta ($\Delta P$), Flow variance, Temperature rise, Total Dynamic Pump Head, Vibration RMS ($V_{RMS} = \sqrt{\frac{1}{N}\sum v_i^2}$), and Fluid Stability Condition.
- **Interactive Visualizations**: Time-series charts for Pressure, Flow, Temperature, Vibration, RPM, and Pressure vs Flow (Pump Operating Curve).
- **Feature Engineering**: Auto-generates rolling mean pressure, pressure deviation, flow variance, thermal rise, vibration RMS, RPM std dev, and motor current variance.

### **Module 2: ML-Based Predictive Maintenance & Visualization**
- **ML Algorithm Selector**: Decision Tree Classifier, Random Forest Classifier, and XGBoost (with automatic graceful fallback to Random Forest if `xgboost` package is uninstalled).
- **80/20 Stratified Split**: Automated train/test data partition with leak-free scaling.
- **Model Performance Metrics**: Accuracy, Precision, Recall, F1 Score, Confusion Matrix (3x3), and Feature Importance ranking.
- **Live Failure Predictor**: Manual input form to evaluate real-time sensor parameters.
- **Status Classification & Risk Gauge**: Classifies health into **NORMAL** (Risk < 35%), **WARNING** (35% $\le$ Risk < 70%), or **POTENTIAL FAILURE** (Risk $\ge$ 70%).
- **Prescriptive Maintenance**: Automated repair prescriptions tailored to identified sensor anomalies (cavitation, bearing friction, seal leakage, motor overload).

---

## 📁 Project Directory Structure

```
c:\Users\tejap\Downloads\ML Website\
│
├── app.py                      # Flask web server & REST API controller
├── config.py                   # Application configuration & security settings
├── generate_sample_data.py     # Physics-based synthetic pump dataset generator (800 records)
├── init_db.py                  # SQLite database initializer & sample seed script
├── requirements.txt            # Python dependencies
├── README.md                   # Capstone presentation & execution guide
├── database.db                 # SQLite database file (generated automatically)
│
├── data/
│   └── sample_pump_data.csv    # 800-record synthetic telemetry dataset
│
├── models/
│   ├── __init__.py
│   ├── predictive_model.py     # Scikit-learn & XGBoost ML pipeline engine
│   └── saved/                  # Saved model joblib binary artifacts
│
├── utils/
│   ├── __init__.py
│   ├── db_helper.py            # SQLite database CRUD operations
│   ├── preprocessing.py        # Missing value, duplicate, outlier, & scaling functions
│   ├── fluid_analysis.py       # Fluid dynamics metrics & Chart.js data formatter
│   └── feature_engineering.py  # Feature extraction pipeline
│
├── templates/
│   ├── base.html               # Shared layout (Sidebar, Topbar, Toast alerts)
│   ├── index.html              # Landing page & Academic Capstone overview
│   ├── dashboard.html          # Executive Industrial Control Dashboard
│   ├── module1.html            # Module 1: Fluid Dynamics & Preprocessing UI
│   ├── module2.html            # Module 2: ML Training & Failure Predictor UI
│   └── dataset.html            # Dataset Management & Telemetry Log UI
│
└── static/
    ├── css/
    │   └── style.css           # Industrial dark dashboard styling
    └── js/
        ├── main.js             # Global UI handlers
        ├── module1.js          # Module 1 dynamic charts & upload handler
        ├── module2.js          # Module 2 model training & prediction form
        └── dashboard.js        # Executive dashboard KPI update polling
```

---

## 🛠️ Installation & Setup Instructions

### Prerequisites
- **Python 3.9+** installed on your system.
- Standard web browser (Chrome, Firefox, Edge).

### Step 1: Install Dependencies
Open terminal or command prompt in the project root folder:
```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database & Sample Telemetry
Run the database initialization script to create tables and generate the synthetic dataset (800 records):
```bash
python init_db.py
```

### Step 3: Run the Flask Web Application
Start the development server:
```bash
python app.py
```
The server will start at `http://127.0.0.1:5000/`.

---

## 🎓 Capstone Presentation Workflow Guide

Follow this sequence for demonstrating the project during your B.Tech Capstone presentation:

1. **Project Landing Page (`/`)**:
   - Showcase the Project Title, Problem Statement, Objectives, and Expected Outcomes.
   - Explain the strict **Two-Module Architecture** (Module 1 & Module 2).

2. **Module 1 – Fluid Dynamics Analysis (`/module1`)**:
   - Point out the dataset upload functionality and the default 800-record CSV telemetry.
   - Click **"Execute Preprocessing"** to demonstrate missing value imputation, duplicate removal, IQR outlier capping, and noise filtering.
   - Walk through the interactive charts (Pressure vs Time, Flow vs Time, Temperature vs Time, Vibration vs Time, RPM vs Time, and the Pressure vs Flow Rate Pump Curve).
   - Show the **Feature Engineering Table** containing the 8 derived ML features.

3. **Module 2 – ML Predictive Maintenance (`/module2`)**:
   - Select an algorithm (Random Forest, Decision Tree, or XGBoost) and click **"Train & Evaluate Model"**.
   - Review the Evaluation Cards (**Accuracy, Precision, Recall, F1 Score**) and the **Confusion Matrix**.
   - Use the **Live Sensor Telemetry Input Form**:
     - *Test Case A (Normal)*: Pressure: 4.2, Flow: 175, Temp: 48, Vibration: 1.2, Current: 18 -> Result: **NORMAL** (Low risk).
     - *Test Case B (Warning)*: Pressure: 2.1, Flow: 140, Temp: 68, Vibration: 3.8, Current: 24 -> Result: **WARNING** (Medium risk, inspection alert).
     - *Test Case C (Failure)*: Pressure: 1.2, Flow: 90, Temp: 88, Vibration: 7.5, Current: 32 -> Result: **POTENTIAL FAILURE** (High risk, immediate maintenance recommendation).

4. **Executive Dashboard (`/dashboard`)**:
   - Highlight the top KPI Cards, real-time multi-sensor telemetry trends, status distribution doughnut chart, and the live prediction log table.

5. **Dataset Management (`/dataset`)**:
   - Inspect raw SQLite sensor database records and uploaded file history.
