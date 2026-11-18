import os
import pandas as pd
from config import Config
from utils.db_helper import init_db, save_dataset_records, get_active_sensor_dataframe
from generate_sample_data import generate_pump_dataset

def initialize_application_db():
    print("Initializing SQLite database...")
    init_db()

    # Check if active dataset exists
    df_active = get_active_sensor_dataframe()
    if df_active.empty:
        print("No active dataset found in SQLite. Generating and populating sample data...")
        if not os.path.exists(Config.SAMPLE_CSV):
            df_sample = generate_pump_dataset(num_records=800, output_path=Config.SAMPLE_CSV)
        else:
            df_sample = pd.read_csv(Config.SAMPLE_CSV)
        
        save_dataset_records(df_sample, filename="sample_pump_data.csv", set_active=True)
        print("Database seeded successfully!")
    else:
        print(f"Active dataset found with {len(df_active)} records.")

if __name__ == '__main__':
    initialize_application_db()
