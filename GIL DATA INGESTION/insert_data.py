from sqlalchemy import create_engine, text
from db.database import engine, Base, ROOT_DATABASE_URL, DB_NAME
from seed_plants import seed_plants
from seed_consumption import seed_consumption
from seed_generation import seed_generation
from seed_settlement_matching import seed_settlement_matching
from seed_slot_summary import seed_slot_summary
from seed_tod_daily_summary import seed_tod_daily_summary
from seed_monthly_banking import seed_monthly_banking

def create_db_if_not_exists():
    # Use a temporary engine to create the database if it doesn't exist
    temp_engine = create_engine(ROOT_DATABASE_URL)
    with temp_engine.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}"))
        print(f"Database '{DB_NAME}' checked/created.")
    temp_engine.dispose()

def init_db():
    print("Creating tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    print("Tables initialized.")

def run_all_seeds():
    print("--- Starting Modular Seeding ---")
    seed_plants()
    seed_consumption()
    seed_generation()
    seed_settlement_matching()
    seed_slot_summary()
    seed_tod_daily_summary()
    seed_monthly_banking()
    print("--- Seeding Completed ---")

if __name__ == "__main__":
    try:
        create_db_if_not_exists()
        init_db()
        run_all_seeds()
        print("Initial setup and seeding completed successfully!")
    except Exception as e:
        print(f"Critical error during setup: {e}")
