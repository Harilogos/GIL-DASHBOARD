import pandas as pd
from db.database import SessionLocal
from db.models import ConsumptionData
from datetime import datetime

def seed_consumption():
    db = SessionLocal()
    try:
        print("Reading consumption data from Excel...")
        file_path = 'AUG_25_CONS.xlsx'
        df = pd.read_excel(file_path)

        # Duplicate prevention: fetch existing keys
        print("Fetching existing consumption record keys...")
        existing_keys = set(db.query(ConsumptionData.consumption_date, ConsumptionData.consumption_time).all())

        print("Processing records...")
        new_records = []
        for index, row in df.iterrows():
            # Date parsing
            if isinstance(row['Date'], datetime):
                cons_date = row['Date'].date()
            else:
                cons_date = datetime.strptime(str(row['Date']).split(' ')[0], '%Y-%m-%d').date()

            # Time parsing (Slot)
            time_str = str(row['Slot'])
            if ':' in time_str:
                cons_time = datetime.strptime(time_str, '%H:%M' if len(time_str.split(':')) == 2 else '%H:%M:%S').time()
            else:
                continue

            # Value parsing (Final KWH) - handling commas if present
            raw_value = str(row['Final KWH']).replace(',', '')
            try:
                value = float(raw_value)
            except ValueError:
                print(f"Skipping row {index}: invalid consumption value {raw_value}")
                continue

            key = (cons_date, cons_time)
            if key not in existing_keys:
                new_records.append(ConsumptionData(
                    consumption_date=cons_date,
                    consumption_time=cons_time,
                    consumption_value=value
                ))
                existing_keys.add(key)

        print(f"Adding {len(new_records)} new consumption records (skipping duplicates)...")
        if new_records:
            db.bulk_save_objects(new_records)
            db.commit()
            print("Consumption data seeded successfully.")
        else:
            print("No new consumption records to add.")
            
    except Exception as e:
        print(f"Error seeding consumption: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_consumption()
