from datetime import datetime
import pandas as pd
import logging
from sqlalchemy import text
from db.database import engine

def normalize_slot_name(slot: str) -> str:
    """Standardize slot names."""
    if not slot: return ""
    return str(slot).strip().upper()

def fetch_tod_data_with_granularity(engine_or_conn, plant_type, start_date, end_date, granularity):
    """Fetch ToD generation and consumption data based on granularity.
    
    - daily:   tod_daily_summary (per day, per tod_slot)
    - monthly: monthly_banking_settlement (per month, per tod_slot)
    - 60min:   settlement_matching aggregated to daily totals per date
    """
    try:
        if granularity == "60min":
            # Aggregate settlement_matching records grouped by date+time, with slot derived from time
            # Slot names match tod_daily_summary: normal, off-peak, peak
            query = text("""
                SELECT 
                    settlement_date as date,
                    CONCAT(settlement_date, ' ', settlement_time) as datetime,
                    SUM(generation_value) as generation_kwh,
                    SUM(allocated_consumption) as consumption_kwh,
                    CASE 
                        WHEN settlement_time >= '18:00:00' AND settlement_time < '22:00:00' THEN 'peak'
                        WHEN settlement_time >= '22:00:00' OR settlement_time < '06:00:00' THEN 'off-peak'
                        ELSE 'normal'
                    END as slot
                FROM settlement_matching
                WHERE settlement_date BETWEEN :start_date AND :end_date
                GROUP BY settlement_date, settlement_time, slot
                ORDER BY settlement_date, settlement_time
            """)
        elif granularity == "daily":
            # Daily data per ToD slot from tod_daily_summary
            query = text("""
                SELECT 
                    summary_date as date,
                    tod_slot as slot,
                    generation_value as generation_kwh,
                    slot_total_consumption as consumption_kwh
                FROM tod_daily_summary
                WHERE summary_date BETWEEN :start_date AND :end_date
                ORDER BY summary_date, tod_slot
            """)
        elif granularity == "monthly":
            # Monthly data per ToD slot from monthly_banking_settlement
            query = text("""
                SELECT 
                    settlement_month as month,
                    tod_slot as slot,
                    generation_value as generation_kwh,
                    slot_total_consumption as consumption_kwh
                FROM monthly_banking_settlement
                WHERE settlement_month BETWEEN DATE_FORMAT(:start_date, '%Y-%m') 
                                          AND DATE_FORMAT(:end_date, '%Y-%m')
                ORDER BY settlement_month, tod_slot
            """)
        else:
            logging.error(f"Invalid granularity: {granularity}")
            return None

        with engine.connect() as conn:
            params = {
                'start_date': start_date,
                'end_date': end_date
            }
            return pd.read_sql(query, conn, params=params)

    except Exception as e:
        logging.error(f"Error fetching ToD data: {e}")
        return None


def fetch_generation_consumption_with_banking_settlement(engine_or_conn, plant_type="ALL"):
    """Fetch monthly aggregated generation, consumption, and settlement data."""
    where_clause = ""
    params = {}
    if plant_type != "ALL":
        where_clause = "WHERE sm.generation_type = :plant_type"
        params = {'plant_type': plant_type}

    query = text(f"""
    SELECT 
        DATE_FORMAT(sm.settlement_date, '%Y-%m') as month,
        SUM(sm.generation_value) as total_supplied_generation,
        SUM(sm.allocated_consumption) as total_consumption,
        SUM(sm.matched_settlement) as total_matched_settlement,
        SUM(sm.surplus_gen_with_banking) as total_settlement_with_banking,
        SUM(GREATEST(0, sm.slot_total_consumption - (sm.matched_settlement + sm.surplus_gen_with_banking))) as total_surplus_demand_after_banking
    FROM settlement_matching sm
    {where_clause}
    GROUP BY month
    ORDER BY month
    """)
    try:
        with engine.connect() as conn:
            return pd.read_sql(query, conn, params=params)
    except Exception as e:
        logging.error(f"Error fetching aggregated data: {e}")
        return None


def fetch_unitwise_monthly_data(engine_or_conn):
    """Fetch unit-wise monthly cost and savings data."""
    # We aggregate from settlement_matching
    # For simplicity, we'll use approximate rates derived from seed_savings_summary.py
    # Grid Var Rate ~ 7.10, RE Rate ~ 3.50, Tax ~ 15%
    # In a real app, these would come from a configuration table.
    
    query = text("""
    SELECT 
        serial_number as unit,
        DATE_FORMAT(settlement_date, '%Y-%m') as month,
        SUM(allocated_consumption) as consumption,
        SUM(matched_settlement + surplus_gen_with_banking) as settlement,
        SUM(allocated_consumption * 7.10) as raw_grid_cost,
        SUM((allocated_consumption - (matched_settlement + surplus_gen_with_banking)) * 7.10 + 
            (matched_settlement + surplus_gen_with_banking) * 3.50) as raw_actual_cost
    FROM settlement_matching
    GROUP BY unit, month
    ORDER BY month, unit
    """)
    
    try:
        with engine.connect() as conn:
            df = pd.read_sql(query, conn)
            
            if df.empty:
                return df
                
            # Apply taxes and calculate savings
            tax_rate = 0.15 # 15% placeholder
            df['grid_cost'] = df['raw_grid_cost'] * (1 + tax_rate)
            df['actual_cost'] = df['raw_actual_cost'] * (1 + tax_rate)
            df['savings'] = df['grid_cost'] - df['actual_cost']
            df['savings_percentage'] = (df['savings'] / df['grid_cost'] * 100).fillna(0)
            
            return df
    except Exception as e:
        logging.error(f"Error fetching unit-wise monthly data: {e}")
        return pd.DataFrame()

def get_connection():
    """Return the SQLAlchemy engine."""
    return engine
