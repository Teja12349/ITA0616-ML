import sqlite3
import json
import pandas as pd
from datetime import datetime
from config import Config

def get_db_connection():
    conn = sqlite3.connect(Config.DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS uploaded_datasets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_time TEXT NOT NULL,
            record_count INTEGER NOT NULL,
            col_count INTEGER NOT NULL,
            is_active INTEGER DEFAULT 0
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id INTEGER,
            timestamp TEXT,
            pressure REAL,
            flow_rate REAL,
            temperature REAL,
            vibration REAL,
            rpm REAL,
            motor_current REAL,
            pump_head REAL,
            operating_hours REAL,
            failure_status INTEGER,
            FOREIGN KEY (dataset_id) REFERENCES uploaded_datasets (id) ON DELETE CASCADE
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            pressure REAL,
            flow_rate REAL,
            temperature REAL,
            vibration REAL,
            rpm REAL,
            motor_current REAL,
            pump_head REAL,
            operating_hours REAL,
            predicted_status TEXT NOT NULL,
            risk_score REAL NOT NULL,
            recommendation TEXT,
            contributing_factors TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS model_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            model_name TEXT NOT NULL,
            accuracy REAL NOT NULL,
            precision REAL NOT NULL,
            recall REAL NOT NULL,
            f1_score REAL NOT NULL,
            confusion_matrix_json TEXT NOT NULL,
            feature_importances_json TEXT,
            trained_at TEXT NOT NULL,
            is_active INTEGER DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

def save_dataset_records(df, filename="sample_pump_data.csv", set_active=True):
    conn = get_db_connection()
    cursor = conn.cursor()

    if set_active:
        cursor.execute("UPDATE uploaded_datasets SET is_active = 0")

    upload_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO uploaded_datasets (filename, upload_time, record_count, col_count, is_active)
        VALUES (?, ?, ?, ?, ?)
    ''', (filename, upload_time, len(df), len(df.columns), 1 if set_active else 0))

    dataset_id = cursor.lastrowid

    # If active, delete old sensor data or tag dataset_id
    if set_active:
        cursor.execute("DELETE FROM sensor_data WHERE dataset_id = ?", (dataset_id,))

    records = []
    for _, row in df.iterrows():
        records.append((
            dataset_id,
            str(row.get('timestamp', '')),
            float(row.get('pressure', 0.0)) if pd.notnull(row.get('pressure')) else None,
            float(row.get('flow_rate', 0.0)) if pd.notnull(row.get('flow_rate')) else None,
            float(row.get('temperature', 0.0)) if pd.notnull(row.get('temperature')) else None,
            float(row.get('vibration', 0.0)) if pd.notnull(row.get('vibration')) else None,
            float(row.get('rpm', 0.0)) if pd.notnull(row.get('rpm')) else None,
            float(row.get('motor_current', 0.0)) if pd.notnull(row.get('motor_current')) else None,
            float(row.get('pump_head', 0.0)) if pd.notnull(row.get('pump_head')) else None,
            float(row.get('operating_hours', 0.0)) if pd.notnull(row.get('operating_hours')) else None,
            int(row.get('failure_status', 0)) if pd.notnull(row.get('failure_status')) else 0
        ))

    cursor.executemany('''
        INSERT INTO sensor_data (
            dataset_id, timestamp, pressure, flow_rate, temperature,
            vibration, rpm, motor_current, pump_head, operating_hours, failure_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', records)

    conn.commit()
    conn.close()
    return dataset_id

def get_active_sensor_dataframe():
    conn = get_db_connection()
    # Get active dataset_id
    active = conn.execute("SELECT id FROM uploaded_datasets WHERE is_active = 1 ORDER BY id DESC LIMIT 1").fetchone()
    if not active:
        conn.close()
        return pd.DataFrame()

    dataset_id = active['id']
    df = pd.read_sql_query("SELECT * FROM sensor_data WHERE dataset_id = ? ORDER BY id ASC", conn, params=(dataset_id,))
    conn.close()
    return df

def save_prediction(input_data, status, risk_score, recommendation, factors):
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute('''
        INSERT INTO predictions (
            timestamp, pressure, flow_rate, temperature, vibration,
            rpm, motor_current, pump_head, operating_hours,
            predicted_status, risk_score, recommendation, contributing_factors
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        now_str,
        input_data.get('pressure'),
        input_data.get('flow_rate'),
        input_data.get('temperature'),
        input_data.get('vibration'),
        input_data.get('rpm'),
        input_data.get('motor_current'),
        input_data.get('pump_head'),
        input_data.get('operating_hours'),
        status,
        risk_score,
        recommendation,
        json.dumps(factors)
    ))

    conn.commit()
    conn.close()

def get_recent_predictions(limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def save_model_result(model_name, metrics, confusion_matrix, feature_importances):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE model_results SET is_active = 0 WHERE model_name = ?", (model_name,))

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO model_results (
            model_name, accuracy, precision, recall, f1_score,
            confusion_matrix_json, feature_importances_json, trained_at, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        model_name,
        metrics['accuracy'],
        metrics['precision'],
        metrics['recall'],
        metrics['f1_score'],
        json.dumps(confusion_matrix),
        json.dumps(feature_importances),
        now_str
    ))
    conn.commit()
    conn.close()

def get_latest_model_results():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM model_results 
        WHERE id IN (SELECT MAX(id) FROM model_results GROUP BY model_name)
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d['confusion_matrix'] = json.loads(d['confusion_matrix_json'])
        d['feature_importances'] = json.loads(d['feature_importances_json']) if d['feature_importances_json'] else {}
        res.append(d)
    return res

def get_datasets_list():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM uploaded_datasets ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]
