import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler

def detect_missing_values(df):
    missing = df.isnull().sum()
    missing_dict = {col: int(val) for col, val in missing.items() if val > 0}
    total_missing = int(missing.sum())
    return {
        'total_missing': total_missing,
        'missing_by_column': missing_dict
    }

def handle_missing_values(df, strategy='mean'):
    df_clean = df.copy()
    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_clean[col].isnull().sum() > 0:
            if strategy == 'mean':
                val = df_clean[col].mean()
            elif strategy == 'median':
                val = df_clean[col].median()
            else:
                val = df_clean[col].ffill().bfill()
            df_clean[col] = df_clean[col].fillna(val)
    return df_clean

def handle_duplicates(df):
    dup_count = int(df.duplicated().sum())
    df_clean = df.drop_duplicates().reset_index(drop=True)
    return df_clean, dup_count

def detect_and_handle_outliers(df, method='iqr', factor=1.5):
    df_clean = df.copy()
    numeric_cols = ['pressure', 'flow_rate', 'temperature', 'vibration', 'rpm', 'motor_current', 'pump_head']
    numeric_cols = [c for c in numeric_cols if c in df_clean.columns]
    
    outliers_detected = {}
    total_outliers = 0

    for col in numeric_cols:
        if method == 'iqr':
            Q1 = df_clean[col].quantile(0.25)
            Q3 = df_clean[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - factor * IQR
            upper_bound = Q3 + factor * IQR
            
            mask = (df_clean[col] < lower_bound) | (df_clean[col] > upper_bound)
            count = int(mask.sum())
            outliers_detected[col] = count
            total_outliers += count

            # Cap outliers to bounds
            df_clean[col] = np.clip(df_clean[col], lower_bound, upper_bound)
        elif method == 'zscore':
            mean = df_clean[col].mean()
            std = df_clean[col].std()
            if std > 0:
                z_scores = np.abs((df_clean[col] - mean) / std)
                mask = z_scores > 3.0
                count = int(mask.sum())
                outliers_detected[col] = count
                total_outliers += count
                # Clip
                df_clean[col] = np.clip(df_clean[col], mean - 3*std, mean + 3*std)

    return df_clean, {'total_outliers': total_outliers, 'outliers_by_col': outliers_detected}

def apply_noise_reduction(df, window_size=3):
    df_clean = df.copy()
    sensor_cols = ['pressure', 'flow_rate', 'temperature', 'vibration', 'rpm', 'motor_current', 'pump_head']
    sensor_cols = [c for c in sensor_cols if c in df_clean.columns]
    
    for col in sensor_cols:
        df_clean[col] = df_clean[col].rolling(window=window_size, min_periods=1).mean()
    return df_clean

def normalize_data(df, method='minmax'):
    df_clean = df.copy()
    numeric_cols = ['pressure', 'flow_rate', 'temperature', 'vibration', 'rpm', 'motor_current', 'pump_head', 'operating_hours']
    numeric_cols = [c for c in numeric_cols if c in df_clean.columns]
    
    if method == 'minmax':
        scaler = MinMaxScaler()
    else:
        scaler = StandardScaler()
        
    df_clean[numeric_cols] = scaler.fit_transform(df_clean[numeric_cols])
    return df_clean

def run_full_preprocessing_pipeline(df, fill_strategy='mean', outlier_method='iqr', scale_method='minmax'):
    initial_rows = len(df)
    initial_cols = len(df.columns)

    missing_info = detect_missing_values(df)
    df_step1 = handle_missing_values(df, strategy=fill_strategy)
    
    df_step2, dup_count = handle_duplicates(df_step1)
    
    df_step3, outlier_info = detect_and_handle_outliers(df_step2, method=outlier_method)
    
    df_step4 = apply_noise_reduction(df_step3, window_size=3)
    
    df_scaled = normalize_data(df_step4, method=scale_method)

    stats = {
        'initial_rows': initial_rows,
        'final_rows': len(df_scaled),
        'missing_values_found': missing_info['total_missing'],
        'duplicates_removed': dup_count,
        'outliers_handled': outlier_info['total_outliers'],
        'cols_processed': initial_cols,
        'preprocessing_steps': [
            'Missing value detection & mean/median imputation',
            'Duplicate record identification & removal',
            'IQR/Z-score outlier capping',
            'Rolling mean noise smoothing filter',
            f'Data scaling using {scale_method.upper()} transformation'
        ]
    }

    return df_step4, df_scaled, stats
