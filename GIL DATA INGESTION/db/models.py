from sqlalchemy import Column, Integer, BigInteger, String, Float, Date, Time, DateTime, Enum, ForeignKey, Index, UniqueConstraint, DECIMAL, text
from sqlalchemy.sql import func
from db.database import Base

class PlantMetadata(Base):
    __tablename__ = 'plant_metadata'
    
    plant_id = Column(Integer, primary_key=True, autoincrement=True)
    plant_name = Column(String(100), nullable=False)
    plant_type = Column(Enum('WIND', 'SOLAR', 'HYBRID'), nullable=False)
    location = Column(String(255))
    capacity_mw = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_plant_type', 'plant_type'),
    )

class WindGeneration(Base):
    __tablename__ = 'wind_generation'
    
    wind_gen_id = Column(BigInteger, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey('plant_metadata.plant_id'), nullable=False)
    serial_number = Column(String(100), nullable=False)
    generation_date = Column(Date, nullable=False)
    generation_time = Column(Time, nullable=False)
    generation_value = Column(DECIMAL(14, 4), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('serial_number', 'generation_date', 'generation_time', name='unique_wind_record'),
        Index('idx_wind_date', 'generation_date'),
        Index('idx_wind_serial', 'serial_number'),
        Index('idx_wind_plant', 'plant_id'),
    )

class SolarGeneration(Base):
    __tablename__ = 'solar_generation'
    
    solar_gen_id = Column(BigInteger, primary_key=True, autoincrement=True)
    plant_id = Column(Integer, ForeignKey('plant_metadata.plant_id'), nullable=False)
    serial_number = Column(String(100), nullable=False)
    generation_date = Column(Date, nullable=False)
    generation_time = Column(Time, nullable=False)
    generation_value = Column(DECIMAL(14, 4), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('serial_number', 'generation_date', 'generation_time', name='unique_solar_record'),
        Index('idx_solar_date', 'generation_date'),
        Index('idx_solar_serial', 'serial_number'),
        Index('idx_solar_plant', 'plant_id'),
    )

class ConsumptionData(Base):
    __tablename__ = 'consumption_data'
    
    consumption_id = Column(BigInteger, primary_key=True, autoincrement=True)
    consumption_date = Column(Date, nullable=False)
    consumption_time = Column(Time, nullable=False)
    consumption_value = Column(DECIMAL(14, 4), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('consumption_date', 'consumption_time', name='unique_consumption'),
        Index('idx_consumption_date', 'consumption_date'),
    )

class SettlementMatching(Base):
    __tablename__ = 'settlement_matching'
    
    matching_id = Column(BigInteger, primary_key=True, autoincrement=True)
    settlement_date = Column(Date, nullable=False)
    settlement_time = Column(Time, nullable=False)
    plant_id = Column(Integer, ForeignKey('plant_metadata.plant_id'), nullable=False)
    serial_number = Column(String(100), nullable=False)
    generation_type = Column(Enum('WIND', 'SOLAR'), nullable=False)
    generation_value = Column(DECIMAL(14, 4), server_default=text('0'))
    slot_total_consumption = Column(DECIMAL(14, 4), server_default=text('0'))
    allocated_consumption = Column(DECIMAL(14, 4), server_default=text('0'))
    surplus_generation = Column(DECIMAL(14, 4), server_default=text('0'))
    surplus_gen_with_banking = Column(DECIMAL(14, 4), server_default=text('0'))
    matched_settlement = Column(DECIMAL(14, 4), server_default=text('0'))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('serial_number', 'settlement_date', 'settlement_time', name='unique_matching_record'),
        Index('idx_matching_date', 'settlement_date'),
        Index('idx_matching_datetime', 'settlement_date', 'settlement_time'),
        Index('idx_matching_serial', 'serial_number'),
        Index('idx_matching_plant', 'plant_id'),
    )

class SlotSummary(Base):
    __tablename__ = 'slot_summary'
    
    slot_summary_id = Column(BigInteger, primary_key=True, autoincrement=True)
    summary_date = Column(Date, nullable=False)
    summary_time = Column(Time, nullable=False)
    generation_value = Column(DECIMAL(14, 4))
    slot_total_consumption = Column(DECIMAL(14, 4))
    allocated_consumption = Column(DECIMAL(14, 4))
    surplus_generation = Column(DECIMAL(14, 4))
    surplus_gen_with_banking = Column(DECIMAL(14, 4))
    matched_settlement = Column(DECIMAL(14, 4))

    __table_args__ = (
        UniqueConstraint('summary_date', 'summary_time', name='unique_slot_summary'),
        Index('idx_slot_summary_date', 'summary_date'),
    )

class TodDailySummary(Base):
    __tablename__ = 'tod_daily_summary'
    
    tod_daily_summary_id = Column(BigInteger, primary_key=True, autoincrement=True)
    summary_date = Column(Date, nullable=False)
    tod_slot = Column(String(100), nullable=False)
    generation_value = Column(DECIMAL(14, 4))
    allocated_consumption = Column(DECIMAL(14, 4))
    matched_settlement = Column(DECIMAL(14, 4))
    surplus_demand = Column(DECIMAL(14, 4))
    surplus_generation = Column(DECIMAL(14, 4))
    surplus_gen_with_banking = Column(DECIMAL(14, 4))
    slot_total_consumption = Column(DECIMAL(14, 4))
    matched_settlement_daily_tod = Column(DECIMAL(14, 4))
    surplus_gen_daily_tod = Column(DECIMAL(14, 4))
    surplus_demand_daily_tod = Column(DECIMAL(14, 4))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('summary_date', 'tod_slot', name='unique_tod_daily'),
        Index('idx_tod_daily_date', 'summary_date'),
    )

class MonthlyBankingSettlement(Base):
    __tablename__ = 'monthly_banking_settlement'
    
    banking_id = Column(BigInteger, primary_key=True, autoincrement=True)
    settlement_month = Column(String(7), nullable=False)
    tod_slot = Column(String(100), nullable=False)
    generation_value = Column(DECIMAL(14, 4))
    allocated_consumption = Column(DECIMAL(14, 4))
    matched_settlement = Column(DECIMAL(14, 4))
    surplus_demand = Column(DECIMAL(14, 4))
    surplus_generation = Column(DECIMAL(14, 4))
    surplus_gen_with_banking = Column(DECIMAL(14, 4))
    slot_total_consumption = Column(DECIMAL(14, 4))
    matched_settlement_daily_tod = Column(DECIMAL(14, 4))
    surplus_gen_daily_tod = Column(DECIMAL(14, 4))
    surplus_demand_daily_tod = Column(DECIMAL(14, 4))
    matched_settlement_intra_monthly = Column(DECIMAL(14, 4))
    surplus_gen_intra_monthly = Column(DECIMAL(14, 4))
    surplus_demand_intra_monthly = Column(DECIMAL(14, 4))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('settlement_month', 'tod_slot', name='unique_month_tod'),
        Index('idx_banking_month', 'settlement_month'),
    )

class SavingsSummary(Base):
    __tablename__ = 'savings_summary'
    
    savings_id = Column(BigInteger, primary_key=True, autoincrement=True)
    settlement_month = Column(Date, nullable=False)
    total_consumption = Column(DECIMAL(14, 4))
    grid_cost = Column(DECIMAL(14, 4))
    actual_cost_with_banking = Column(DECIMAL(14, 4))
    savings_with_banking = Column(DECIMAL(14, 4))
    savings_pct_with_banking = Column(DECIMAL(6, 2))
    actual_cost_without_banking = Column(DECIMAL(14, 4))
    savings_without_banking = Column(DECIMAL(14, 4))
    savings_pct_without_banking = Column(DECIMAL(6, 2))
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('settlement_month', name='unique_savings_month'),
    )
