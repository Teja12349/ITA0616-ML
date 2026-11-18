import os
import json
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename

from config import Config
from utils.db_helper import (
    init_db, save_dataset_records, get_active_sensor_dataframe,
    save_prediction, get_recent_predictions, get_latest_model_results,
    get_datasets_list
)
from utils.preprocessing import run_full_preprocessing_pipeline
from utils.fluid_analysis import calculate_fluid_dynamics_metrics, prepare_fluid_chart_data
from utils.feature_engineering import generate_ml_features
from models.predictive_model import train_and_evaluate_model, predict_single_instance
from generate_sample_data import generate_pump_dataset

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database on startup
with app.app_context():
    init_db()
    # Check if active dataset exists, if not generate sample
    df_check = get_active_sensor_dataframe()
    if df_check.empty:
        if not os.path.exists(Config.SAMPLE_CSV):
            df_gen = generate_pump_dataset(num_records=800, output_path=Config.SAMPLE_CSV)
        else:
            df_gen = pd.read_csv(Config.SAMPLE_CSV)
        save_dataset_records(df_gen, filename="sample_pump_data.csv", set_active=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# ==========================================
# PAGE ROUTES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/module1')
def module1():
    return render_template('module1.html')

@app.route('/module2')
def module2():
    return render_template('module2.html')

@app.route('/dataset')
def dataset_management():
    datasets = get_datasets_list()
    df_active = get_active_sensor_dataframe()
    sample_records = df_active.head(50).to_dict('records') if not df_active.empty else []
    return render_template('dataset.html', datasets=datasets, active_count=len(df_active), sample_records=sample_records)


# ==========================================
# API ENDPOINTS
# ==========================================

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file submitted in request.'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected.'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['DATA_DIR'], filename)
        file.save(filepath)

        try:
            df = pd.read_csv(filepath)
            required_cols = {'pressure', 'flow_rate', 'temperature', 'vibration'}
            if not required_cols.issubset(df.columns):
                return jsonify({
                    'success': False, 
                    'error': f'Invalid CSV format. File must contain sensor columns: {", ".join(required_cols)}'
                }), 400

            dataset_id = save_dataset_records(df, filename=filename, set_active=True)
            return jsonify({
                'success': True,
                'filename': filename,
                'record_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'message': f'Successfully uploaded {filename} with {len(df)} records.'
            })
        except Exception as e:
            return jsonify({'success': False, 'error': f'Failed to process CSV file: {str(e)}'}), 500
    else:
        return jsonify({'success': False, 'error': 'Only .csv format files are permitted.'}), 400

@app.route('/api/reset-sample-data', methods=['POST'])
def reset_sample_data():
    try:
        df_sample = generate_pump_dataset(num_records=800, output_path=Config.SAMPLE_CSV)
        dataset_id = save_dataset_records(df_sample, filename="sample_pump_data.csv", set_active=True)
        return jsonify({
            'success': True,
            'filename': 'sample_pump_data.csv',
            'record_count': len(df_sample),
            'column_count': len(df_sample.columns),
            'message': f'Reset to synthetic sample pump dataset with {len(df_sample)} records.'
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/preprocess', methods=['GET', 'POST'])
def preprocess_data():
    df = get_active_sensor_dataframe()
    if df.empty:
        return jsonify({'success': False, 'error': 'No active sensor dataset found. Please upload or load sample data.'}), 400

    fill_strategy = request.args.get('fill_strategy', 'mean')
    outlier_method = request.args.get('outlier_method', 'iqr')
    scale_method = request.args.get('scale_method', 'minmax')

    df_cleaned, df_scaled, stats = run_full_preprocessing_pipeline(
        df, fill_strategy=fill_strategy, outlier_method=outlier_method, scale_method=scale_method
    )

    # Return summary stats & sample table preview
    preview_data = df_cleaned.head(20).to_dict('records')
    
    return jsonify({
        'success': True,
        'stats': stats,
        'preview': preview_data
    })

@app.route('/api/fluid-analysis', methods=['GET'])
def fluid_analysis():
    df = get_active_sensor_dataframe()
    if df.empty:
        return jsonify({'success': False, 'error': 'No active dataset available for fluid analysis.'}), 400

    metrics = calculate_fluid_dynamics_metrics(df)
    chart_data = prepare_fluid_chart_data(df)

    return jsonify({
        'success': True,
        'metrics': metrics,
        'chart_data': chart_data
    })

@app.route('/api/feature-engineering', methods=['GET'])
def feature_engineering():
    df = get_active_sensor_dataframe()
    if df.empty:
        return jsonify({'success': False, 'error': 'No active dataset available.'}), 400

    df_features, preview_table = generate_ml_features(df)
    
    return jsonify({
        'success': True,
        'feature_count': len(df_features.columns),
        'record_count': len(df_features),
        'table_preview': preview_table
    })

@app.route('/api/train-model', methods=['POST'])
def train_model():
    df = get_active_sensor_dataframe()
    if df.empty:
        return jsonify({'success': False, 'error': 'No dataset available to train machine learning model.'}), 400

    data = request.get_json() or {}
    model_type = data.get('model_type', 'Random Forest')

    try:
        results = train_and_evaluate_model(df, model_type=model_type)
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Model training failed: {str(e)}'}), 500

@app.route('/api/predict', methods=['POST'])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No input parameters provided.'}), 400

    try:
        result = predict_single_instance(data)
        
        # Save prediction record to SQLite DB
        save_prediction(
            input_data=data,
            status=result['predicted_status'],
            risk_score=result['risk_score'],
            recommendation=result['recommendation'],
            factors=result['contributing_factors']
        )

        return jsonify({
            'success': True,
            'prediction': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': f'Prediction execution error: {str(e)}'}), 500

@app.route('/api/model-results', methods=['GET'])
def model_results():
    results = get_latest_model_results()
    return jsonify({
        'success': True,
        'models': results
    })

@app.route('/api/predictions', methods=['GET'])
def predictions_history():
    recent = get_recent_predictions(limit=25)
    return jsonify({
        'success': True,
        'predictions': recent
    })

@app.route('/api/dashboard-summary', methods=['GET'])
def dashboard_summary():
    df = get_active_sensor_dataframe()
    if df.empty:
        return jsonify({'success': False, 'error': 'No dataset active.'}), 400

    metrics = calculate_fluid_dynamics_metrics(df)
    chart_data = prepare_fluid_chart_data(df, sample_limit=80)
    models = get_latest_model_results()
    recent_preds = get_recent_predictions(limit=10)

    # Compute current status distribution
    if 'failure_status' in df.columns:
        status_counts = df['failure_status'].value_counts().to_dict()
        normal_cnt = int(status_counts.get(0, 0))
        warn_cnt = int(status_counts.get(1, 0))
        fail_cnt = int(status_counts.get(2, 0))
    else:
        normal_cnt, warn_cnt, fail_cnt = len(df), 0, 0

    # Latest record KPI readings
    latest_rec = df.iloc[-1].to_dict() if not df.empty else {}

    # Risk % estimate from latest readings
    latest_vib = float(latest_rec.get('vibration', 1.0))
    latest_temp = float(latest_rec.get('temperature', 45.0))
    risk_estimate = min(100.0, max(5.0, (latest_vib * 7.5 + (latest_temp - 40) * 1.2)))

    if risk_estimate < 35.0:
        current_status = "NORMAL"
    elif risk_estimate < 70.0:
        current_status = "WARNING"
    else:
        current_status = "POTENTIAL FAILURE"

    return jsonify({
        'success': True,
        'kpis': {
            'current_status': current_status,
            'risk_estimate': round(risk_estimate, 1),
            'latest_pressure': round(float(latest_rec.get('pressure', 0)), 2),
            'latest_flow': round(float(latest_rec.get('flow_rate', 0)), 2),
            'latest_temp': round(float(latest_rec.get('temperature', 0)), 2),
            'latest_vibration': round(float(latest_rec.get('vibration', 0)), 2),
            'latest_rpm': round(float(latest_rec.get('rpm', 0)), 1),
            'record_count': len(df)
        },
        'status_distribution': {
            'NORMAL': normal_cnt,
            'WARNING': warn_cnt,
            'POTENTIAL_FAILURE': fail_cnt
        },
        'chart_data': chart_data,
        'latest_model': models[0] if models else None,
        'recent_predictions': recent_preds
    })


if __name__ == '__main__':
    print("Starting Industrial Pump & Compressor Predictive Maintenance Web Application...")
    app.run(host='127.0.0.1', port=5000, debug=True)
