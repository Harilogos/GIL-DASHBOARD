import pandas as pd
from db.database import SessionLocal
from db.models import TodDailySummary
from datetime import datetime

def seed_tod_daily_summary():
    db = SessionLocal()
    try:
        print("Reading TOD daily summary data from Excel...")
        file_path = 'settlement_AUG.xlsx'
        df = pd.read_excel(file_path, sheet_name='TOD_Wise_Summary')

        # Duplicate prevention: fetch existing keys (summary_date, tod_slot)
        print("Fetching existing TOD daily summary record keys...")
        existing_keys = set(db.query(TodDailySummary.summary_date, TodDailySummary.tod_slot).all())

        print("Processing records...")
        new_records = []
        for index, row in df.iterrows():
            # Date parsing
            if isinstance(row['Date'], datetime):
                s_date = row['Date'].date()
            else:
                s_date = datetime.strptime(str(row['Date']).split(' ')[0], '%Y-%m-%d').date()

            tod_slot = str(row['TOD_slot']).strip()

            # Helper to clean and convert to float
            def to_float(val):
                if pd.isna(val): return 0.0
                try:
                    return float(str(val).replace(',', ''))
                except:
                    return 0.0

            key = (s_date, tod_slot)
            if key not in existing_keys:
                new_records.append(TodDailySummary(
                    summary_date=s_date,
                    tod_slot=tod_slot,
                    generation_value=to_float(row['Generation_value']),
                    allocated_consumption=to_float(row['allocated_consumption']),
                    matched_settlement=to_float(row['matched_settlement']),
                    surplus_demand=to_float(row['surplus_demand']),
                    surplus_generation=to_float(row['surplus_generation']),
                    surplus_gen_with_banking=to_float(row['surplus_gen_with_banking']),
                    slot_total_consumption=to_float(row['Slot_Total_Consumption']),
                    matched_settlement_daily_tod=to_float(row['matched_settlement_daily_tod']),
                    surplus_gen_daily_tod=to_float(row['surplus_gen_daily_tod']),
                    surplus_demand_daily_tod=to_float(row['surplus_demand_daily_tod'])
                ))
                existing_keys.add(key)

        print(f"Adding {len(new_records)} new TOD daily summary records (skipping duplicates)...")
        if new_records:
            db.bulk_save_objects(new_records)
            db.commit()
            print("TOD daily summary data seeded successfully.")
        else:
            print("No new records to add.")
            
    except Exception as e:
        print(f"Error seeding TOD daily summary: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_tod_daily_summary()
