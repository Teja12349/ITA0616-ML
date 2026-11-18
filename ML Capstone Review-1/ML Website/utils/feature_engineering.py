import pandas as pd
import numpy as np

def generate_ml_features(df):
    if df.empty:
        return pd.DataFrame(), []

    df_feat = df.copy()

    # Calculate engineered fluid features
    mean_p_overall = df_feat['pressure'].mean() if 'pressure' in df_feat.columns else 0.0
    
    # 1. Mean pressure (rolling 5-period window)
    df_feat['mean_pressure'] = df_feat['pressure'].rolling(window=5, min_periods=1).mean()
    
    # 2. Pressure difference (deviation from mean operational pressure)
    df_feat['pressure_diff'] = df_feat['pressure'] - mean_p_overall
    
    # 3. Flow variation (rolling std dev of flow rate)
    df_feat['flow_variation'] = df_feat['flow_rate'].rolling(window=5, min_periods=1).std().fillna(0)
    
    # 4. Temperature rise (baseline 40°C fluid operating temperature)
    df_feat['temperature_rise'] = df_feat['temperature'] - 40.0
    
    # 5. Vibration RMS (rolling root-mean-square of vibration over 5 steps)
    df_feat['vibration_rms'] = df_feat['vibration'].rolling(window=5, min_periods=1).apply(
        lambda x: np.sqrt(np.mean(x ** 2)), raw=True
    ).fillna(df_feat['vibration'])
    
    # 6. RPM variation (rolling std dev of RPM)
    df_feat['rpm_variation'] = df_feat['rpm'].rolling(window=5, min_periods=1).std().fillna(0)
    
    # 7. Motor current variation (deviation from nominal 18A current)
    df_feat['motor_current_var'] = df_feat['motor_current'] - 18.0
    
    # 8. Operating hours
    if 'operating_hours' not in df_feat.columns:
        df_feat['operating_hours'] = 100.0

    feature_cols = [
        'mean_pressure',
        'pressure_diff',
        'flow_variation',
        'temperature_rise',
        'vibration_rms',
        'rpm_variation',
        'motor_current_var',
        'operating_hours'
    ]

    # Fill any remaining NaNs
    df_feat[feature_cols] = df_feat[feature_cols].fillna(0.0)

    # Format table summary preview (first 15 rows)
    preview_table = []
    for idx, row in df_feat.head(20).iterrows():
        preview_table.append({
            'index': idx + 1,
            'timestamp': str(row.get('timestamp', f'Step {idx+1}')),
            'mean_pressure': round(float(row['mean_pressure']), 2),
            'pressure_diff': round(float(row['pressure_diff']), 2),
            'flow_variation': round(float(row['flow_variation']), 2),
            'temperature_rise': round(float(row['temperature_rise']), 2),
            'vibration_rms': round(float(row['vibration_rms']), 3),
            'rpm_variation': round(float(row['rpm_variation']), 2),
            'motor_current_var': round(float(row['motor_current_var']), 2),
            'operating_hours': round(float(row['operating_hours']), 1),
            'failure_status': int(row.get('failure_status', 0))
        })

    return df_feat, preview_table
