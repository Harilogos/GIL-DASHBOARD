import streamlit as st
import pandas as pd
import logging
from utils.data_fetching import (
    fetch_generation_consumption_with_banking_settlement, 
    fetch_unitwise_monthly_data,
    get_connection
)
from utils.visualization import (
    plot_generation_vs_consumption,
    plot_total_grid_vs_actual_cost_bar_chart
)

# Initialize connection
conn = get_connection()

def display_unitwise_monthly_bill_analysis(selected_plant):
    """Display monthly bill analysis aggregated by plant."""
    unitwise_monthly_data = fetch_unitwise_monthly_data(conn)
    if unitwise_monthly_data is not None and not unitwise_monthly_data.empty:
        st.subheader("💰 Grid Cost vs Actual Cost")
        fig_bar = plot_total_grid_vs_actual_cost_bar_chart(
            df=unitwise_monthly_data,
            client_name=selected_plant
        )
        if fig_bar:
            st.plotly_chart(fig_bar, width='stretch')
        else:
            st.warning("⚠️ Unable to generate the bar chart.")
            logging.warning("Unable to generate the bar chart.")
    else:
        st.warning("⚠️ Error fetching monthly cost data for the selected period.")

def display_summary_dashboard():
    """Display generation vs consumption chart with metrics and plant selection."""
    # Create layout with dropdown on the right
    st.subheader("Generation, Consumption & Settlement Breakdown")
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns([3, 1])
   
    with col2:
        selected_plant = st.selectbox(
            "Select Plant Type:",
            ["ALL", "SOLAR", "WIND"],
            index=0,
            key="plant_type_selector"
        )

    # Fetch data based on selection
    df = fetch_generation_consumption_with_banking_settlement(conn, selected_plant)

    if df is not None and not df.empty:
       
        
        fig = plot_generation_vs_consumption(
            df=df,
            plant_display_name=selected_plant
        )
        if fig:
            st.plotly_chart(fig, width='stretch')
        else:
            logging.error("Failed to generate the interactive chart.")
            st.warning("⚠️ Unable to generate the interactive chart.")
        
        # Display Metrics
        total_generation_mwh = df['total_supplied_generation'].sum() / 1000
        total_consumption_mwh = df['total_consumption'].sum() / 1000
        total_settlement = df['total_matched_settlement'].sum() + df['total_settlement_with_banking'].sum()
        replacement_percentage_with_banking = (total_settlement / df['total_consumption'].sum()) * 100 if df['total_consumption'].sum() > 0 else 0
        total_surplus_demand_after_banking_mwh = df['total_surplus_demand_after_banking'].sum() / 1000
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Generation (MWh)", f"{total_generation_mwh:.2f}")
        with col2:
            st.metric("Total Consumption (MWh)", f"{total_consumption_mwh:.2f}")
        with col3:
            st.metric("Total Replacement (%)", f"{replacement_percentage_with_banking:.2f}%")
        with col4:
            st.metric("Surplus Demand (MWh)", f"{total_surplus_demand_after_banking_mwh:.2f}", help="Surplus demand after considering banking settlement")
        
        # Aggregated Bill Analysis Section
        display_unitwise_monthly_bill_analysis(selected_plant)
        
    else:
        st.warning(f"⚠️ No data available for {selected_plant} plant type.")

def show_summary():
    """Function to display the Summary page."""
    st.title("Summary")
    st.divider()
    display_summary_dashboard()

# Define pages for navigation
pg = st.navigation([
    st.Page(show_summary, title="Summary", icon="📊", default=True),
    st.Page("pages/2_Generation_&_Consumption.py", title="Generation & Consumption", icon="⚡"),
    st.Page("pages/3_Bill_Analysis.py", title="Bill Analysis", icon="💰"),
])

# Set page config
st.set_page_config(
    page_title="GIL Dashboard",
    page_icon="⚡",
    layout="wide"
)

# Run navigation
pg.run()
