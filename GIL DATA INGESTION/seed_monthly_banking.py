import pandas as pd
from db.database import SessionLocal
from db.models import MonthlyBankingSettlement


def seed_monthly_banking():
    db = SessionLocal()
    try:
        print("Reading monthly banking summary data from Excel...")
        file_path = 'settlement_AUG.xlsx'
        df = pd.read_excel(file_path, sheet_name='Monthly_Summary')

        # Since the sheet doesn't have a date, we use August 2025 as per file name
        settlement_month = "2025-08"

        # Duplicate prevention: fetch existing keys (settlement_month, tod_slot)
        print("Fetching existing monthly banking record keys...")
        existing_keys = set(db.query(MonthlyBankingSettlement.settlement_month, MonthlyBankingSettlement.tod_slot).all())

        print("Processing records...")
        new_records = []
        for index, row in df.iterrows():
            tod_slot = str(row['TOD_slot']).strip()

            # Helper to clean and convert to float
            def to_float(val):
                if pd.isna(val): return 0.0
                try:
                    return float(str(val).replace(',', ''))
                except:
                    return 0.0

            key = (settlement_month, tod_slot)
            if key not in existing_keys:
                new_records.append(MonthlyBankingSettlement(
                    settlement_month=settlement_month,
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
                    surplus_demand_daily_tod=to_float(row['surplus_demand_daily_tod']),
                    matched_settlement_intra_monthly=to_float(row['matched_settlement_intra_monthly']),
                    surplus_gen_intra_monthly=to_float(row['surplus_gen_intra_monthly']),
                    surplus_demand_intra_monthly=to_float(row['surplus_demand_intra_monthly'])
                ))
                existing_keys.add(key)

        print(f"Adding {len(new_records)} new monthly banking records (skipping duplicates)...")
        if new_records:
            db.bulk_save_objects(new_records)
            db.commit()
            print("Monthly banking data seeded successfully.")
        else:
            print("No new records to add.")
            
    except Exception as e:
        print(f"Error seeding monthly banking: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_monthly_banking()
