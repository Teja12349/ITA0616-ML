import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

def generate_scenario_dataset(scenario_name, num_records, status_code, filename):
    np.random.seed(hash(scenario_name) % 1000000)
    start_time = datetime.now() - timedelta(hours=num_records)
    timestamps = [(start_time + timedelta(minutes=15*i)).strftime('%Y-%m-%d %H:%M:%S') for i in range(num_records)]

    pressures = []
    flow_rates = []
    temperatures = []
    vibrations = []
    rpms = []
    motor_currents = []
    pump_heads = []
    operating_hours = []

    base_hours = 2500.0

    for i in range(num_records):
        base_hours += 0.25
        operating_hours.append(round(base_hours, 2))

        if status_code == 0:  # NORMAL OPERATING SCENARIO
            q = np.random.normal(185.0, 5.0)
            h = 56.0 - 0.0005 * (q ** 2) + np.random.normal(0, 0.4)
            p = (h * 0.0981) + np.random.normal(0, 0.05)
            t = np.random.normal(46.5, 1.5)
            v = np.random.normal(1.15, 0.15)
            rpm = np.random.normal(2960, 20)
            curr = np.random.normal(17.8, 0.4)

        elif status_code == 1:  # CAVITATION & SUCTION DEGRADATION (WARNING)
            # Declining pressure and fluctuating flow rate
            q = np.random.normal(135.0, 15.0)
            h = 42.0 - 0.0006 * (q ** 2) + np.random.normal(0, 1.2)
            p = (h * 0.0981) + np.random.normal(0, 0.25)
            t = np.random.normal(66.0, 3.5)
            v = np.random.normal(3.95, 0.45)
            rpm = np.random.normal(2860, 45)
            curr = np.random.normal(23.5, 1.2)

        else:  # SEVERE BEARING UNBALANCE & THERMAL FAILURE (POTENTIAL FAILURE)
            # Escalating temperature and heavy vibration
            q = np.random.normal(85.0, 22.0)
            h = 28.0 - 0.0008 * (q ** 2) + np.random.normal(0, 2.0)
            p = (h * 0.0981) + np.random.normal(0, 0.4)
            t = np.random.normal(87.5, 5.5)
            v = np.random.normal(7.85, 0.85)
            rpm = np.random.normal(2680, 95)
            curr = np.random.normal(33.2, 2.1)

        pressures.append(round(max(0.2, p), 2))
        flow_rates.append(round(max(5.0, q), 2))
        temperatures.append(round(max(20.0, t), 2))
        vibrations.append(round(max(0.1, v), 2))
        rpms.append(round(max(500.0, rpm), 1))
        motor_currents.append(round(max(1.0, curr), 2))
        pump_heads.append(round(max(2.0, h), 2))

    df = pd.DataFrame({
        'timestamp': timestamps,
        'pressure': pressures,
        'flow_rate': flow_rates,
        'temperature': temperatures,
        'vibration': vibrations,
        'rpm': rpms,
        'motor_current': motor_currents,
        'pump_head': pump_heads,
        'operating_hours': operating_hours,
        'failure_status': [status_code] * num_records
    })

    file_path = os.path.join(DATA_DIR, filename)
    df.to_csv(file_path, index=False)
    print(f"Created scenario dataset '{scenario_name}' ({num_records} rows) at {file_path}")

if __name__ == '__main__':
    generate_scenario_dataset("Centrifugal Pump Baseline (Normal)", 100, 0, "test_pump_normal_baseline.csv")
    generate_scenario_dataset("Cavitation & Flow Restriction (Warning)", 100, 1, "test_cavitation_warning.csv")
    generate_scenario_dataset("Bearing Wear & Thermal Breakdown (Failure)", 100, 2, "test_bearing_failure_critical.csv")
