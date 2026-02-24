import pandas as pd
from db.database import SessionLocal
from db.models import PlantMetadata, WindGeneration, SolarGeneration
from datetime import datetime

def seed_generation():
    db = SessionLocal()
    try:
        print("Reading generation data from Excel...")
        file_path = 'Generation_AUG-25.xlsx'
        df = pd.read_excel(file_path)

        # Using hardcoded plant_id = 1 as requested
        plant_id = 1
        
        # Check if plant exists
        if not db.query(PlantMetadata).filter_by(plant_id=plant_id).first():
            print(f"Plant with ID {plant_id} not found. Please run seed_plants.py first.")
            return

        print("Fetching existing record keys to prevent duplicates...")
        existing_wind = set(db.query(WindGeneration.serial_number, WindGeneration.generation_date, WindGeneration.generation_time).all())
        existing_solar = set(db.query(SolarGeneration.serial_number, SolarGeneration.generation_date, SolarGeneration.generation_time).all())

        print("Processing records...")
        wind_records = []
        solar_records = []

        for index, row in df.iterrows():
            # Date and Time parsing
            if isinstance(row['Date'], datetime):
                gen_date = row['Date'].date()
            else:
                gen_date = datetime.strptime(str(row['Date']).split(' ')[0], '%Y-%m-%d').date()
            
            # Time format handles HH:MM or HH:MM:SS
            time_str = str(row['slot'])
            if ':' in time_str:
                gen_time = datetime.strptime(time_str, '%H:%M' if len(time_str.split(':')) == 2 else '%H:%M:%S').time()
            else:
                continue

            serial = str(row['serial_number'])
            value = float(row['final kwh units'])
            gen_type = str(row['generation_type']).upper()

            # Create a key for duplicate checking
            key = (serial, gen_date, gen_time)

            if gen_type == 'WIND':
                if key not in existing_wind:
                    wind_records.append(WindGeneration(
                        plant_id=plant_id,
                        serial_number=serial,
                        generation_date=gen_date,
                        generation_time=gen_time,
                        generation_value=value
                    ))
                    existing_wind.add(key) # Add to set to prevent internal duplicates
            elif gen_type == 'SOLAR':
                if key not in existing_solar:
                    solar_records.append(SolarGeneration(
                        plant_id=plant_id,
                        serial_number=serial,
                        generation_date=gen_date,
                        generation_time=gen_time,
                        generation_value=value
                    ))
                    existing_solar.add(key)

        print(f"Filtered records: Adding {len(wind_records)} new wind and {len(solar_records)} new solar records (skipping duplicates).")
        
        # Using bulk insert for performance
        if wind_records:
            db.bulk_save_objects(wind_records)
        if solar_records:
            db.bulk_save_objects(solar_records)
            
        db.commit()
        print("Generation data seeded successfully.")
    except Exception as e:
        print(f"Error seeding generation: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_generation()
