import numpy as np
import pandas as pd

def calculate_fluid_dynamics_metrics(df):
    if df.empty:
        return {}

    p = df['pressure'].dropna()
    q = df['flow_rate'].dropna()
    temp = df['temperature'].dropna()
    vib = df['vibration'].dropna()
    head = df['pump_head'].dropna()
    rpm = df['rpm'].dropna()
    curr = df['motor_current'].dropna()

    p_min, p_max, p_mean, p_std = float(p.min()), float(p.max()), float(p.mean()), float(p.std())
    q_min, q_max, q_mean, q_std = float(q.min()), float(q.max()), float(q.mean()), float(q.std())
    t_min, t_max, t_mean, t_std = float(temp.min()), float(temp.max()), float(temp.mean()), float(temp.std())
    head_min, head_max, head_mean = float(head.min()), float(head.max()), float(head.mean())

    pressure_diff = p_max - p_min
    vibration_rms = float(np.sqrt(np.mean(vib ** 2))) if len(vib) > 0 else 0.0

    # Determine overall fluid dynamics operating condition summary
    conditions = []
    if t_max > 75.0:
        conditions.append("Thermal Overload Risk Detected")
    if vibration_rms > 4.0:
        conditions.append("High Mechanical Vibration / Bearing Wear")
    if (q_mean > 160 and head_mean < 40):
        conditions.append("Potential Cavitation / Head Loss Zone")
    
    if not conditions:
        operating_condition = "Optimal Fluid Dynamic Stability (Normal)"
    else:
        operating_condition = " | ".join(conditions)

    metrics = {
        'pressure_stats': {
            'min': round(p_min, 2),
            'max': round(p_max, 2),
            'mean': round(p_mean, 2),
            'std': round(p_std, 2),
            'diff': round(pressure_diff, 2)
        },
        'flow_stats': {
            'min': round(q_min, 2),
            'max': round(q_max, 2),
            'mean': round(q_mean, 2),
            'std': round(q_std, 2)
        },
        'temp_stats': {
            'min': round(t_min, 2),
            'max': round(t_max, 2),
            'mean': round(t_mean, 2),
            'std': round(t_std, 2)
        },
        'pump_head_stats': {
            'min': round(head_min, 2),
            'max': round(head_max, 2),
            'mean': round(head_mean, 2)
        },
        'vibration_rms': round(vibration_rms, 3),
        'pressure_difference': round(pressure_diff, 2),
        'operating_condition': operating_condition
    }

    return metrics

def prepare_fluid_chart_data(df, sample_limit=150):
    if df.empty:
        return {}

    # Downsample if needed for smooth responsive rendering
    if len(df) > sample_limit:
        step = len(df) // sample_limit
        df_sample = df.iloc[::step].copy()
    else:
        df_sample = df.copy()

    timestamps = df_sample['timestamp'].astype(str).tolist() if 'timestamp' in df_sample.columns else list(range(len(df_sample)))

    return {
        'timestamps': timestamps,
        'pressure': [round(x, 2) for x in df_sample['pressure'].fillna(0).tolist()],
        'flow_rate': [round(x, 2) for x in df_sample['flow_rate'].fillna(0).tolist()],
        'temperature': [round(x, 2) for x in df_sample['temperature'].fillna(0).tolist()],
        'vibration': [round(x, 2) for x in df_sample['vibration'].fillna(0).tolist()],
        'rpm': [round(x, 2) for x in df_sample['rpm'].fillna(0).tolist()],
        'motor_current': [round(x, 2) for x in df_sample['motor_current'].fillna(0).tolist()],
        'pump_head': [round(x, 2) for x in df_sample['pump_head'].fillna(0).tolist()],
        'pressure_vs_flow': [
            {'x': round(q, 2), 'y': round(p, 2), 'head': round(h, 2)}
            for q, p, h in zip(df_sample['flow_rate'], df_sample['pressure'], df_sample['pump_head'])
        ]
    }
