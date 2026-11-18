import json
import sqlite3
from datetime import datetime, timedelta
from config import Config

def seed_prediction_logs():
    conn = sqlite3.connect(Config.DATABASE)
    cursor = conn.cursor()

    # Clear existing prediction test logs if needed or add to them
    cursor.execute("DELETE FROM predictions")

    now = datetime.now()

    sample_predictions = [
        # Normal operations
        {
            "offset_minutes": 5,
            "p": 4.35, "q": 182.4, "t": 47.8, "v": 1.12, "rpm": 2955, "curr": 17.9, "head": 53.2, "hrs": 2450.5,
            "status": "NORMAL", "risk": 8.5,
            "rec": "Equipment operating within normal fluid dynamics conditions. Maintain routine monitoring schedule.",
            "factors": ["All sensor parameters are within acceptable baseline bounds."]
        },
        {
            "offset_minutes": 25,
            "p": 4.20, "q": 178.0, "t": 48.5, "v": 1.25, "rpm": 2948, "curr": 18.2, "head": 51.8, "hrs": 2449.2,
            "status": "NORMAL", "risk": 11.2,
            "rec": "Equipment operating within normal fluid dynamics conditions. Maintain routine monitoring schedule.",
            "factors": ["All sensor parameters are within acceptable baseline bounds."]
        },
        {
            "offset_minutes": 60,
            "p": 4.10, "q": 175.5, "t": 49.2, "v": 1.40, "rpm": 2940, "curr": 18.5, "head": 50.5, "hrs": 2448.0,
            "status": "NORMAL", "risk": 14.8,
            "rec": "Equipment operating within normal fluid dynamics conditions. Maintain routine monitoring schedule.",
            "factors": ["All sensor parameters are within acceptable baseline bounds."]
        },
        # Warning states - Mild Cavitation & Thermal elevation
        {
            "offset_minutes": 120,
            "p": 2.85, "q": 142.0, "t": 67.5, "v": 3.85, "rpm": 2865, "curr": 24.2, "head": 41.0, "hrs": 2446.5,
            "status": "WARNING", "risk": 54.5,
            "rec": "Abnormal operating parameters detected. Elevated thermal or vibration signature observed. Schedule inspection within 48 hours.",
            "factors": ["Temperature (67.5 °C) exceeds safe operational limit (65 °C)", "Vibration (3.85 mm/s) exceeds recommended ISO 10816 threshold (3.0 mm/s)"]
        },
        {
            "offset_minutes": 180,
            "p": 2.90, "q": 145.5, "t": 66.0, "v": 3.60, "rpm": 2870, "curr": 23.8, "head": 42.5, "hrs": 2445.0,
            "status": "WARNING", "risk": 48.0,
            "rec": "Abnormal operating parameters detected. Elevated thermal or vibration signature observed. Schedule inspection within 48 hours.",
            "factors": ["Temperature (66.0 °C) exceeds safe operational limit (65 °C)", "Vibration (3.60 mm/s) exceeds recommended ISO 10816 threshold (3.0 mm/s)"]
        },
        {
            "offset_minutes": 240,
            "p": 2.40, "q": 130.0, "t": 71.2, "v": 4.20, "rpm": 2840, "curr": 25.5, "head": 38.0, "hrs": 2443.5,
            "status": "WARNING", "risk": 66.0,
            "rec": "Abnormal operating parameters detected. Elevated thermal or vibration signature observed. Schedule inspection within 48 hours.",
            "factors": ["Temperature (71.2 °C) exceeds safe operational limit (65 °C)", "Vibration (4.20 mm/s) exceeds recommended ISO 10816 threshold (3.0 mm/s)", "Motor Current (25.5 A) indicates electric motor overload (> 25 A)"]
        },
        # Potential Failure states - Heavy vibration & Overheating
        {
            "offset_minutes": 360,
            "p": 1.45, "q": 88.0, "t": 88.5, "v": 7.95, "rpm": 2680, "curr": 33.5, "head": 26.5, "hrs": 2440.0,
            "status": "POTENTIAL FAILURE", "risk": 92.5,
            "rec": "High failure risk detected (severe cavitation, impeller unbalance, or thermal breakdown imminent). Immediate maintenance inspection recommended.",
            "factors": ["Pressure (1.45 bar) outside normal range (2.0 - 8.0 bar)", "Temperature (88.5 °C) exceeds safe operational limit (65 °C)", "Vibration (7.95 mm/s) exceeds recommended ISO 10816 threshold (3.0 mm/s)", "Motor Current (33.5 A) indicates electric motor overload (> 25 A)", "Flow Rate (88.0 L/min) is critically below design capacity"]
        },
        {
            "offset_minutes": 480,
            "p": 1.60, "q": 92.5, "t": 85.0, "v": 7.20, "rpm": 2710, "curr": 32.0, "head": 29.0, "hrs": 2438.0,
            "status": "POTENTIAL FAILURE", "risk": 88.0,
            "rec": "High failure risk detected (severe cavitation, impeller unbalance, or thermal breakdown imminent). Immediate maintenance inspection recommended.",
            "factors": ["Pressure (1.60 bar) outside normal range (2.0 - 8.0 bar)", "Temperature (85.0 °C) exceeds safe operational limit (65 °C)", "Vibration (7.20 mm/s) exceeds recommended ISO 10816 threshold (3.0 mm/s)", "Motor Current (32.0 A) indicates electric motor overload (> 25 A)"]
        },
        {
            "offset_minutes": 600,
            "p": 4.40, "q": 184.0, "t": 46.5, "v": 1.10, "rpm": 2960, "curr": 17.5, "head": 54.0, "hrs": 2435.0,
            "status": "NORMAL", "risk": 7.2,
            "rec": "Equipment operating within normal fluid dynamics conditions. Maintain routine monitoring schedule.",
            "factors": ["All sensor parameters are within acceptable baseline bounds."]
        },
        {
            "offset_minutes": 720,
            "p": 4.30, "q": 181.0, "t": 47.0, "v": 1.18, "rpm": 2950, "curr": 17.8, "head": 53.0, "hrs": 2433.0,
            "status": "NORMAL", "risk": 9.0,
            "rec": "Equipment operating within normal fluid dynamics conditions. Maintain routine monitoring schedule.",
            "factors": ["All sensor parameters are within acceptable baseline bounds."]
        }
    ]

    for item in sample_predictions:
        t_str = (now - timedelta(minutes=item["offset_minutes"])).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO predictions (
                timestamp, pressure, flow_rate, temperature, vibration,
                rpm, motor_current, pump_head, operating_hours,
                predicted_status, risk_score, recommendation, contributing_factors
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            t_str, item["p"], item["q"], item["t"], item["v"],
            item["rpm"], item["curr"], item["head"], item["hrs"],
            item["status"], item["risk"], item["rec"], json.dumps(item["factors"])
        ))

    conn.commit()
    conn.close()
    print(f"Successfully seeded {len(sample_predictions)} recent prediction log entries into SQLite database.")

if __name__ == '__main__':
    seed_prediction_logs()
