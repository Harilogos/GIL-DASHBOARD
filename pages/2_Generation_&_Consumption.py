import streamlit as st
import pandas as pd
import logging
from datetime import datetime, timedelta
from utils.data_fetching import fetch_tod_data_with_granularity, normalize_slot_name, get_connection
from utils.visualization import plot_tod_generation_consumption_lines, SLOT_METADATA, convert_dates_to_string

# Initialize connection
conn = get_connection()

def display_tod_generation_consumption_lines(selected_plant):
    """
    Display ToD generation vs consumption line/bar charts with improved error handling.
    """
    try:
        if not selected_plant or not selected_plant.strip():
            st.error("❌ Please select a valid plant.")
            return

        if "date_range1" not in st.session_state:
            st.session_state.date_range1 = None
        if "generate_required" not in st.session_state:
            st.session_state.generate_required = False

        col1, col2, col3 = st.columns([0.8, 3, 0.8])

        #  Granularity selection
        with col1:
            granularity = st.selectbox(
                "Select Granularity:",
                options=["daily", "60min", "monthly"],
                index=0,
                key="tod_granularity_select"
            )

        #  Date selector + Generate button in same row
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

        # First and last day of previous month
        first_day_current_month = today.replace(day=1)
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        first_day_prev_month = last_day_prev_month.replace(day=1)

        min_date = datetime(2025, 4, 1)
        max_date = today + timedelta(days=365)

        #  Default initialization -> previous month
        if st.session_state.date_range1 is None:
            st.session_state.date_range1 = (
                first_day_prev_month.date(),
                last_day_prev_month.date()
            )
            st.session_state.generate_required = False  # auto-load on first render

        with col3:
            selected_range = st.date_input(
                label="Select Date Range",
                value=st.session_state.date_range1,
                min_value=min_date,
                max_value=max_date,
                key="date_range_tab2"
            )

        #  Handle single vs tuple selection
        prev_start, prev_end = st.session_state.date_range1
        if isinstance(selected_range, tuple) and len(selected_range) == 2:
            start_date_val, end_date_val = selected_range
        elif isinstance(selected_range, tuple) and len(selected_range) == 1:
            start_date_val, end_date_val = selected_range[0], selected_range[0]
        else:
            # Only start selected → keep previous end
            start_date_val, end_date_val = selected_range, prev_end # type: ignore

        new_range = (start_date_val, end_date_val)

        #  Detect change -> require generate button
        if new_range != st.session_state.date_range1:
            st.session_state.date_range1 = new_range
            st.session_state.generate_required = True

        start_date = datetime.combine(st.session_state.date_range1[0], datetime.min.time())
        end_date = datetime.combine(st.session_state.date_range1[1], datetime.min.time())
        start_date_str, end_date_str = convert_dates_to_string(start_date, end_date)

        #  ToD Slot Filters
        selected_slots = []
        if granularity in ["60min", "daily"]:
            with col2:
                st.write("Select TOD Slots:")
                all_slots = list(SLOT_METADATA.keys())
                if not all_slots:
                    st.error("❌ No TOD slots configured in SLOT_METADATA.")
                    return

                with st.container():
                    slot_cols = st.columns(len(all_slots))
                    for i, slot in enumerate(all_slots):
                        with slot_cols[i]:
                            checkbox_key = f"tod_slot_{slot}_{granularity}_{i}"
                            if st.checkbox(slot, value=True, key=checkbox_key):
                                selected_slots.append(slot)

                    if not selected_slots:
                        st.warning("⚠️ At least one TOD slot must be selected. Defaulting to all slots.")
                        selected_slots = all_slots

        with st.spinner(f"Fetching ToD data with {granularity} granularity..."):
            df = fetch_tod_data_with_granularity(
                conn, selected_plant.strip(), start_date, end_date, granularity
            )

        if df is not None and not df.empty:
            # Only filter by slot for daily (60min slots are time-derived, not from SLOT_METADATA)
            if granularity == "daily" and 'slot' in df.columns:
                df['slot'] = df['slot'].apply(normalize_slot_name)
                df = df[df['slot'].isin(selected_slots)]

            if not df.empty:
                fig = plot_tod_generation_consumption_lines(
                    df=df,
                    plant_display_name=selected_plant,
                    start_date=start_date_str,
                    end_date=end_date_str,
                    granularity=granularity,
                    selected_slots=selected_slots if granularity in ["daily", "60min"] else None
                )
                if fig:
                    st.plotly_chart(fig, width='stretch')
                else:
                    st.error("❌ Unable to generate the ToD chart. Please check the plotting function.")
            else:
                st.warning("⚠️ No data available for selected slots/date range.")
        else:
            st.warning(f"⚠️ Error fetching data from {start_date_str} to {end_date_str}.")

    except Exception as display_error:
        logging.error(f"Error in displaying ToD generation and consumption: {display_error}")
        st.error(f"❌ An error occurred while displaying the ToD dashboard: {display_error}")

def main():
    st.set_page_config(page_title="GIL Dashboard - Generation & Consumption", layout="wide")
    st.title("Generation & Consumption")
    st.divider()

    # Plant selection
    col1, col2 = st.columns([3, 1])
    with col2:
        selected_plant = st.selectbox(
            "Select Plant Type:",
            ["ALL", "SOLAR", "WIND"],
            index=0,
            key="plant_type_select_gen_page"
        )
    
    display_tod_generation_consumption_lines(selected_plant)

if __name__ == "__main__":
    main()
