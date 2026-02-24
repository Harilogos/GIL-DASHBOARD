import pandas as pd
from db.database import SessionLocal
from db.models import SavingsSummary, MonthlyBankingSettlement
from datetime import datetime
from sqlalchemy import func
import decimal

def seed_savings_summary():
    db = SessionLocal()
    try:
        print("Reading bill calculation data from Excel...")
        file_path = 'calculate_discom_bill.xlsx'
        df = pd.read_excel(file_path)

        for index, row in df.iterrows():
            month_str = str(row['month']).strip()  # e.g., '2025-08'
            month_date = datetime.strptime(month_str, '%Y-%m').date()
            
            # Helper to convert to Decimal
            def to_dec(val):
                if pd.isna(val): return decimal.Decimal('0')
                try:
                    return decimal.Decimal(str(val).replace(',', ''))
                except:
                    return decimal.Decimal('0')

            total_cons = to_dec(row['total_consumption'])
            grid_rate = to_dec(row['grid_cost_rate'])
            re_rate = to_dec(row['renewable_cost_rate'])
            
            # Tariffs/Charges
            tax_rate = to_dec(row['tax_tariff'])
            fppca = to_dec(row['fuel_cost_adj_charges_tariff'])
            pandg = to_dec(row['PandG_surcharge_tariff'])
            wheeling = to_dec(row['manual_wheeling_energy_charge_tariff'])
            manual_energy = to_dec(row['manual_energy_charge_tariff'])
            
            # Demand charges
            demand_charges = to_dec(row['demand_charges_tariff']) * to_dec(row['demand_charges_kwh'])

            # Combined Grid Variable Rate
            grid_var_rate = grid_rate + fppca + pandg + wheeling + manual_energy

            # 1. GRID COST (If 100% Grid)
            grid_cost_before_tax = (total_cons * grid_var_rate) + demand_charges
            total_grid_cost = grid_cost_before_tax * (1 + tax_rate)

            # Fetch matched units from DB for this month
            matched_data = db.query(
                func.sum(MonthlyBankingSettlement.matched_settlement_daily_tod).label('without_banking'),
                func.sum(MonthlyBankingSettlement.matched_settlement_intra_monthly).label('with_banking')
            ).filter(MonthlyBankingSettlement.settlement_month == month_str).first()

            matched_without_banking = to_dec(matched_data.without_banking) if matched_data else decimal.Decimal('0')
            matched_with_banking = to_dec(matched_data.with_banking) if matched_data else decimal.Decimal('0')

            print(f"Month: {month_str}")
            print(f"Matched (No Banking): {matched_without_banking}")
            print(f"Matched (With Banking): {matched_with_banking}")

            # 2. ACTUAL COST WITH BANKING
            # Matched units pay RE rate + taxes/charges (assuming RE rate is all-inclusive for the unit?)
            # Usually, matched units might only pay RE Rate + Wheeling + Tax.
            # Let's assume: Matched units pay (re_rate + wheeling), Unmatched pay full grid rate.
            # Actually, RE units often bypass some surcharges but not all.
            # For simplicity, we'll use: Matched * re_rate + Unmatched * grid_var_rate
            
            re_cost_with = matched_with_banking * (re_rate + wheeling) # RE + Wheeling
            grid_cost_with = (total_cons - matched_with_banking) * grid_var_rate
            actual_with_banking = (re_cost_with + grid_cost_with + demand_charges) * (1 + tax_rate)

            # 3. ACTUAL COST WITHOUT BANKING
            re_cost_without = matched_without_banking * (re_rate + wheeling)
            grid_cost_without = (total_cons - matched_without_banking) * grid_var_rate
            actual_without_banking = (re_cost_without + grid_cost_without + demand_charges) * (1 + tax_rate)

            # Savings
            savings_with = total_grid_cost - actual_with_banking
            savings_pct_with = (savings_with / total_grid_cost * 100) if total_grid_cost > 0 else 0

            savings_without = total_grid_cost - actual_without_banking
            savings_pct_without = (savings_without / total_grid_cost * 100) if total_grid_cost > 0 else 0

            # DB Record
            existing = db.query(SavingsSummary).filter_by(settlement_month=month_date).first()
            if existing:
                print(f"Updating existing record for {month_str}")
                existing.total_consumption = total_cons
                existing.grid_cost = total_grid_cost
                existing.actual_cost_with_banking = actual_with_banking
                existing.savings_with_banking = savings_with
                existing.savings_pct_with_banking = savings_pct_with
                existing.actual_cost_without_banking = actual_without_banking
                existing.savings_without_banking = savings_without
                existing.savings_pct_without_banking = savings_pct_without
            else:
                print(f"Adding new record for {month_str}")
                new_record = SavingsSummary(
                    settlement_month=month_date,
                    total_consumption=total_cons,
                    grid_cost=total_grid_cost,
                    actual_cost_with_banking=actual_with_banking,
                    savings_with_banking=savings_with,
                    savings_pct_with_banking=savings_pct_with,
                    actual_cost_without_banking=actual_without_banking,
                    savings_without_banking=savings_without,
                    savings_pct_without_banking=savings_pct_without
                )
                db.add(new_record)

        db.commit()
        print("Savings summary updated successfully.")

    except Exception as e:
        print(f"Error seeding savings summary: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_savings_summary()
