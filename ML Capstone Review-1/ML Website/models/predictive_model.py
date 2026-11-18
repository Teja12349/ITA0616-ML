import os
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# Check XGBoost availability with fallback to Random Forest
XGBOOST_AVAILABLE = False
try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False

from config import Config
from utils.feature_engineering import generate_ml_features
from utils.db_helper import save_model_result

# Feature column definitions
FEATURE_COLUMNS = [
    'pressure',
    'flow_rate',
    'temperature',
    'vibration',
    'rpm',
    'motor_current',
    'pump_head',
    'operating_hours'
]

STATUS_MAP = {
    0: 'NORMAL',
    1: 'WARNING',
    2: 'POTENTIAL FAILURE'
}

RECOMMENDATIONS = {
    'NORMAL': "Equipment operating within normal fluid dynamics conditions. Maintain routine monitoring schedule.",
    'WARNING': "Abnormal operating parameters detected. Elevated thermal or vibration signature observed. Schedule inspection within 48 hours.",
    'POTENTIAL FAILURE': "High failure risk detected (severe cavitation, impeller unbalance, or thermal breakdown imminent). Immediate maintenance inspection recommended."
}

def train_and_evaluate_model(df, model_type='Random Forest'):
    if df.empty or 'failure_status' not in df.columns:
        raise ValueError("Dataset is empty or missing 'failure_status' column.")

    # Prepare features and target
    X = df[FEATURE_COLUMNS].copy()
    y = df['failure_status'].astype(int)

    # Impute any missing values
    X = X.fillna(X.mean())

    # 80/20 train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
    )

    # Preprocessing scaler
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    fallback_notice = None

    # Instantiate selected algorithm
    if model_type == 'Decision Tree':
        clf = DecisionTreeClassifier(max_depth=6, min_samples_split=4, random_state=42)
    elif model_type == 'XGBoost':
        if XGBOOST_AVAILABLE:
            clf = XGBClassifier(n_estimators=100, max_depth=5, learning_rate=0.1, random_state=42, eval_metric='mlogloss')
        else:
            clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
            fallback_notice = "XGBoost library is not installed in the environment. Automatically fell back to Random Forest."
            model_type = 'Random Forest (Fallback)'
    else:  # Default Random Forest
        clf = RandomForestClassifier(n_estimators=100, max_depth=8, random_state=42)
        model_type = 'Random Forest'

    # Fit model
    clf.fit(X_train_scaled, y_train)

    # Predictions
    y_pred = clf.predict(X_test_scaled)

    # Calculate metrics
    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred, average='weighted', zero_division=0))
    rec = float(recall_score(y_test, y_pred, average='weighted', zero_division=0))
    f1 = float(f1_score(y_test, y_pred, average='weighted', zero_division=0))

    cm = confusion_matrix(y_test, y_pred, labels=[0, 1, 2]).tolist()

    # Extract feature importances
    if hasattr(clf, 'feature_importances_'):
        importances = {col: float(val) for col, val in zip(FEATURE_COLUMNS, clf.feature_importances_)}
    else:
        importances = {col: 1.0 / len(FEATURE_COLUMNS) for col in FEATURE_COLUMNS}

    # Save artifacts to disk
    os.makedirs(Config.SAVED_MODELS_DIR, exist_ok=True)
    joblib.dump(clf, os.path.join(Config.SAVED_MODELS_DIR, 'latest_model.pkl'))
    joblib.dump(scaler, os.path.join(Config.SAVED_MODELS_DIR, 'latest_scaler.pkl'))
    joblib.dump(model_type, os.path.join(Config.SAVED_MODELS_DIR, 'latest_model_name.pkl'))

    metrics = {
        'accuracy': round(acc, 4),
        'precision': round(prec, 4),
        'recall': round(rec, 4),
        'f1_score': round(f1, 4)
    }

    # Save metrics to SQLite database
    save_model_result(model_type, metrics, cm, importances)

    return {
        'model_name': model_type,
        'metrics': metrics,
        'confusion_matrix': cm,
        'feature_importances': importances,
        'fallback_notice': fallback_notice,
        'test_count': len(y_test),
        'train_count': len(y_train)
    }

def load_trained_model():
    model_path = os.path.join(Config.SAVED_MODELS_DIR, 'latest_model.pkl')
    scaler_path = os.path.join(Config.SAVED_MODELS_DIR, 'latest_scaler.pkl')
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        clf = joblib.load(model_path)
        scaler = joblib.load(scaler_path)
        return clf, scaler
    return None, None

def predict_single_instance(input_dict):
    clf, scaler = load_trained_model()
    
    # Feature vector setup as DataFrame with feature names
    data_dict = {col: [float(input_dict.get(col, 0.0))] for col in FEATURE_COLUMNS}
    X_single = pd.DataFrame(data_dict)
    
    if clf is not None and scaler is not None:
        X_scaled = scaler.transform(X_single)
        pred_class = int(clf.predict(X_scaled)[0])
        
        if hasattr(clf, 'predict_proba'):
            probs = clf.predict_proba(X_scaled)[0]
            # Risk calculation: weighted sum of warning & potential failure probabilities
            # Classes present in model
            classes = clf.classes_
            prob_dict = {c: 0.0 for c in [0, 1, 2]}
            for c, p in zip(classes, probs):
                prob_dict[c] = p
            
            risk_score = float(prob_dict.get(1, 0.0) * 50.0 + prob_dict.get(2, 0.0) * 100.0)
        else:
            risk_score = 0.0 if pred_class == 0 else (55.0 if pred_class == 1 else 90.0)
    else:
        # Rule-based fallback if no model trained yet
        p = input_dict.get('pressure', 4.0)
        temp = input_dict.get('temperature', 50.0)
        vib = input_dict.get('vibration', 1.5)
        
        if temp > 80.0 or vib > 6.0:
            pred_class = 2
            risk_score = 88.0
        elif temp > 65.0 or vib > 3.0 or p < 2.0:
            pred_class = 1
            risk_score = 52.0
        else:
            pred_class = 0
            risk_score = 12.0

    status_str = STATUS_MAP.get(pred_class, 'NORMAL')
    recommendation = RECOMMENDATIONS.get(status_str, "Routine monitoring.")

    # Identify contributing out-of-bounds parameters
    contributing_factors = []
    if input_dict.get('pressure', 0) < 2.0 or input_dict.get('pressure', 0) > 8.0:
        contributing_factors.append(f"Pressure ({input_dict.get('pressure')} bar) outside normal range (2.0 - 8.0 bar)")
    if input_dict.get('temperature', 0) > 65.0:
        contributing_factors.append(f"Temperature ({input_dict.get('temperature')} °C) exceeds safe operational limit (65 °C)")
    if input_dict.get('vibration', 0) > 3.0:
        contributing_factors.append(f"Vibration ({input_dict.get('vibration')} mm/s) exceeds recommended ISO 10816 threshold (3.0 mm/s)")
    if input_dict.get('motor_current', 0) > 25.0:
        contributing_factors.append(f"Motor Current ({input_dict.get('motor_current')} A) indicates electric motor overload (> 25 A)")
    if input_dict.get('flow_rate', 0) < 100.0:
        contributing_factors.append(f"Flow Rate ({input_dict.get('flow_rate')} L/min) is critically below design capacity")

    if not contributing_factors:
        contributing_factors.append("All sensor parameters are within acceptable baseline bounds.")

    return {
        'predicted_class': pred_class,
        'predicted_status': status_str,
        'risk_score': round(risk_score, 1),
        'recommendation': recommendation,
        'contributing_factors': contributing_factors
    }
