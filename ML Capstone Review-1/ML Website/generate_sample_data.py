import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import Config

def generate_pump_dataset(num_records=800, output_path=None):
    np.random.seed(42)
    
    start_time = datetime.now() - timedelta(hours=num_records)
    timestamps = [start_time + timedelta(hours=i) for i in range(num_records)]
    
    # Base operational ranges
    # 70% Normal, 20% Warning, 10% Potential Failure
    status_choices = [0, 1, 2]
    status_probs = [0.70, 0.20, 0.10]
    
    statuses = np.random.choice(status_choices, size=num_records, p=status_probs)
    # Ensure sequential degradation trends in blocks for realistic plotting
    # Sort or smooth the statuses to make time series graphs look like real industrial degradation
    statuses = pd.Series(statuses).rolling(window=5, min_periods=1).max().astype(int).values

    pressures = []
    flow_rates = []
    temperatures = []
    vibrations = []
    rpms = []
    motor_currents = []
    pump_heads = []
    operating_hours = []

    cum_hours = 1200.0

    for i in range(num_records):
        st = statuses[i]
        cum_hours += np.random.uniform(0.8, 1.2)
        operating_hours.append(round(cum_hours, 1))

        if st == 0:  # NORMAL
            rpm = np.random.normal(2950, 45)
            # Pressure vs Flow rate following Affinity / Pump Head curve
            flow = np.random.normal(180, 12)
            # Head H = H0 - k * Q^2
            head = 55.0 - 0.0005 * (flow ** 2) + np.random.normal(0, 0.8)
            pressure = (head * 0.0981) + np.random.normal(0, 0.1) # bar approx
            temp = np.random.normal(48, 3.0)
            vib = np.random.normal(1.2, 0.25)
            curr = np.random.normal(18.5, 0.8)

        elif st == 1:  # WARNING (Degradation / Mild Cavitation / Bearing Wear)
            rpm = np.random.normal(2850, 80)
            flow = np.random.normal(145, 20)
            head = 44.0 - 0.0006 * (flow ** 2) + np.random.normal(0, 1.5)
            pressure = (head * 0.0981) + np.random.normal(0, 0.3)
            temp = np.random.normal(68, 5.0)
            vib = np.random.normal(3.8, 0.6)
            curr = np.random.normal(24.0, 1.8)

        else:  # POTENTIAL FAILURE (Severe Cavitation / Severe Vibration / Overheating)
            rpm = np.random.normal(2700, 150)
            flow = np.random.normal(95, 30)
            head = 30.0 - 0.0008 * (flow ** 2) + np.random.normal(0, 2.5)
            pressure = (head * 0.0981) + np.random.normal(0, 0.6)
            temp = np.random.normal(88, 7.0)
            vib = np.random.normal(7.2, 1.1)
            curr = np.random.normal(32.5, 3.2)

        # Introduce occasional synthetic noise / outliers to showcase preprocessing
        if np.random.rand() < 0.02:
            vib += np.random.choice([8.0, -2.0])
        if np.random.rand() < 0.015:
            temp += np.random.choice([35.0, -25.0])

        pressures.append(round(max(0.5, pressure), 2))
        flow_rates.append(round(max(10.0, flow), 2))
        temperatures.append(round(max(15.0, temp), 2))
        vibrations.append(round(max(0.1, vib), 2))
        rpms.append(round(max(500, rpm), 1))
        motor_currents.append(round(max(2.0, curr), 2))
        pump_heads.append(round(max(5.0, head), 2))

    df = pd.DataFrame({
        'timestamp': [t.strftime('%Y-%m-%d %H:%M:%S') for t in timestamps],
        'pressure': pressures,
        'flow_rate': flow_rates,
        'temperature': temperatures,
        'vibration': vibrations,
        'rpm': rpms,
        'motor_current': motor_currents,
        'pump_head': pump_heads,
        'operating_hours': operating_hours,
        'failure_status': statuses
    })

    # Add a few duplicate rows and NaN missing values for preprocessing demonstration
    # Make ~10 missing values
    missing_indices = np.random.choice(df.index, size=12, replace=False)
    for idx in missing_indices[:6]:
        df.loc[idx, 'pressure'] = np.nan
    for idx in missing_indices[6:]:
        df.loc[idx, 'vibration'] = np.nan

    # Add 4 duplicate rows
    dup_rows = df.iloc[:4].copy()
    df = pd.concat([df, dup_rows], ignore_index=True)

    if output_path is None:
        output_path = Config.SAMPLE_CSV

    df.to_csv(output_path, index=False)
    print(f"Generated sample dataset with {len(df)} records at {output_path}")
    return df

if __name__ == '__main__':
    generate_pump_dataset()
