import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'capstone-fluid-dynamics-ml-secret-key-2026'
    DATABASE = os.path.join(BASE_DIR, 'database.db')
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    SAMPLE_CSV = os.path.join(DATA_DIR, 'sample_pump_data.csv')
    SAVED_MODELS_DIR = os.path.join(BASE_DIR, 'models', 'saved')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'csv'}

os.makedirs(Config.DATA_DIR, exist_ok=True)
os.makedirs(Config.SAVED_MODELS_DIR, exist_ok=True)
