from db.database import SessionLocal
from db.models import PlantMetadata

def seed_plants():
    db = SessionLocal()
    try:
        # Check if we already have data
        if db.query(PlantMetadata).first():
            print("Plant metadata already exists. Skipping.")
            return

        print("Seeding plant metadata (ID=1)...")
        plant = PlantMetadata(
            plant_id=1,
            plant_name='GIL', 
            plant_type='HYBRID', 
            location='MAHARASHTRA', 
            capacity_mw=5.0
        )
        db.add(plant)
        db.commit()
        print("Successfully seeded plant with ID 1.")
    except Exception as e:
        print(f"Error seeding plants: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_plants()
