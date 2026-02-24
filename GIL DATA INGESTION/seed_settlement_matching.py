import pandas as pd
from db.database import SessionLocal
from db.models import SettlementMatching, PlantMetadata
from datetime import datetime

def seed_settlement_matching():
    db = SessionLocal()
    try:
        print("Reading settlement matching data from Excel...")
        file_path = 'settlement_AUG.xlsx'
        # Using the identified sheet name
        df = pd.read_excel(file_path, sheet_name='Slot_Wise_Data')

        # Using hardcoded plant_id = 1
        plant_id = 1
        if not db.query(PlantMetadata).filter_by(plant_id=plant_id).first():
            print(f"Plant with ID {plant_id} not found. Please run seed_plants.py first.")
            return

        # Duplicate prevention: fetch existing keys (serial_number, settlement_date, settlement_time)
        print("Fetching existing settlement matching record keys...")
        existing_keys = set(db.query(
            SettlementMatching.serial_number, 
            SettlementMatching.settlement_date, 
            SettlementMatching.settlement_time
        ).all())

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

            serial = str(row['serial_number'])
            gen_type = str(row['generation_type']).upper()
            
            # Helper to clean and convert to float
            def to_float(val):
                if pd.isna(val): return 0.0
                try:
                    return float(str(val).replace(',', ''))
                except:
                    return 0.0

            key = (serial, s_date, s_time)
            if key not in existing_keys:
                new_records.append(SettlementMatching(
                    settlement_date=s_date,
                    settlement_time=s_time,
                    plant_id=plant_id,
                    serial_number=serial,
                    generation_type=gen_type,
                    generation_value=to_float(row['Generation_value']),
                    slot_total_consumption=to_float(row['Slot_Total_Consumption']),
                    allocated_consumption=to_float(row['Allocated_Consumption']),
                    surplus_generation=to_float(row['Surplus_Generation']),
                    surplus_gen_with_banking=to_float(row['surplus_gen_with_banking']),
                    matched_settlement=to_float(row['Matched_Settlement'])
                ))
                existing_keys.add(key)

        print(f"Adding {len(new_records)} new settlement matching records (skipping duplicates)...")
        if new_records:
            # Using chunks for very large datasets if needed, but bulk_save_objects is generally fine
            db.bulk_save_objects(new_records)
            db.commit()
            print("Settlement matching data seeded successfully.")
        else:
            print("No new records to add.")
            
    except Exception as e:
        print(f"Error seeding settlement matching: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_settlement_matching()
