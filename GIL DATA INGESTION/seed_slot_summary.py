import pandas as pd
from db.database import SessionLocal
from db.models import SlotSummary
from datetime import datetime

def seed_slot_summary():
    db = SessionLocal()
    try:
        print("Reading slot summary data from Excel...")
        file_path = 'settlement_AUG.xlsx'
        df = pd.read_excel(file_path, sheet_name='Date_Slot_Summary')

        # Duplicate prevention: fetch existing keys (summary_date, summary_time)
        print("Fetching existing slot summary record keys...")
        existing_keys = set(db.query(SlotSummary.summary_date, SlotSummary.summary_time).all())

        print("Processing records...")
        new_records = []
        for index, row in df.iterrows():
            # Date parsing
            if isinstance(row['Date'], datetime):
                s_date = row['Date'].date()
            else:
                s_date = datetime.strptime(str(row['Date']).split(' ')[0], '%Y-%m-%d').date()

            # Time parsing (Slot)
            time_str = str(row['Slot']).strip()
            if time_str == '24:00' or time_str == '24:00:00':
                s_time = datetime.strptime('00:00', '%H:%M').time()
            elif ':' in time_str:
                try:
                    s_time = datetime.strptime(time_str, '%H:%M' if len(time_str.split(':')) == 2 else '%H:%M:%S').time()
                except ValueError:
                    print(f"Skipping row {index}: invalid time format {time_str}")
                    continue
            else:
                continue

            # Helper to clean and convert to float
            def to_float(val):
                if pd.isna(val): return 0.0
                try:
                    return float(str(val).replace(',', ''))
                except:
                    return 0.0

            key = (s_date, s_time)
            if key not in existing_keys:
                new_records.append(SlotSummary(
                    summary_date=s_date,
                    summary_time=s_time,
                    generation_value=to_float(row['Generation_value']),
                    slot_total_consumption=to_float(row['Slot_Total_Consumption']),
                    allocated_consumption=to_float(row['allocated_consumption']),
                    surplus_generation=to_float(row['surplus_generation']),
                    surplus_gen_with_banking=to_float(row['surplus_gen_with_banking']),
                    matched_settlement=to_float(row['matched_settlement'])
                ))
                existing_keys.add(key)

        print(f"Adding {len(new_records)} new slot summary records (skipping duplicates)...")
        if new_records:
            db.bulk_save_objects(new_records)
            db.commit()
            print("Slot summary data seeded successfully.")
        else:
            print("No new records to add.")
            
    except Exception as e:
        print(f"Error seeding slot summary: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_slot_summary()
