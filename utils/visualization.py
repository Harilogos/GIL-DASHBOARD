import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
from typing import Optional

def plot_generation_vs_consumption(
    df: pd.DataFrame,
    plant_display_name: str
):
    """
    Plots monthly total supplied generation, total consumption, and settlements 
    (stacked as matched settlement + settlement with banking).
    """
    if df is None:
        import logging
        logging.error("plot_generation_vs_consumption received None as DataFrame")
        return None
    if df.empty:
        import logging
        logging.warning("plot_generation_vs_consumption received an empty DataFrame")
        return None
    required_columns = [
        'month', 
        'total_supplied_generation', 
        'total_consumption', 
        'total_matched_settlement', 
        'total_settlement_with_banking'
    ]
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        # We'll log error and return None instead of raising ValueError to keep app running
        import logging
        logging.error(f"DataFrame missing required columns: {missing}. Required were: {required_columns}")
        return None

    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['month']):
        df['month'] = pd.to_datetime(df['month'], errors='coerce')
    
    # Filter out any rows where date conversion failed
    df = df.dropna(subset=['month'])
    
    if df.empty:
        import logging
        logging.warning("DataFrame is empty after processing (date conversion/dropna)")
        return None
    
    # Create formatted month strings for hover
    df['month_str'] = df['month'].dt.strftime('%b %Y')
    
    # Calculate total settlement and percentage
    df['total_settlement'] = df['total_matched_settlement'] + df['total_settlement_with_banking']
    df['matched_settlement_pct'] = (df['total_matched_settlement'] / df['total_consumption'] * 100).fillna(0)
    df['banking_settlement_pct'] = (df['total_settlement_with_banking'] / df['total_consumption'] * 100).fillna(0)
    df['replacement_pct'] = (df['total_settlement'] / df['total_consumption'] * 100).fillna(0)
    
    # Function to format values for display on bars
    def format_value_for_bar(value):
        if value >= 1000000:
            return f"{value/1000000:.1f}M"
        elif value >= 1000:
            return f"{value/1000:.1f}K"
        else:
            return f"{value:.1f}"
    
    # Dynamic bar width calculation based on number of months
    num_months = len(df)
    
    # Base width in days - adjust this value as needed
    if num_months <= 6:
        base_width_days = 6
    elif num_months <= 12:
        base_width_days = 4
    elif num_months <= 24:
        base_width_days = 2
    else:
        base_width_days = max(2, 48 // num_months)  # Minimum 2 days width
    
    bar_width_ms = base_width_days * 24 * 60 * 60 * 1000
    
    # Calculate positions for the 3 bars per month
    df['x_generation'] = df['month'] - pd.to_timedelta(bar_width_ms, unit='ms')
    df['x_consumption'] = df['month']  # Center bar
    df['x_settlement'] = df['month'] + pd.to_timedelta(bar_width_ms, unit='ms')
    
    fig = make_subplots(rows=1, cols=1)
    
    # Color palette - Green family
    colors = {
        'generation': '#4CAF50',      # Green
        'consumption': "#CE3A3A",     # Red (as requested for consumption)
        'matched_settlement': "#3B9BA0",    # Teal
        'banking_settlement': "#214A86"     # Navy
    }
    
    # Generation
    fig.add_trace(go.Bar(
        x=df['x_generation'],
        y=df['total_supplied_generation'],
        name="Generation",
        width=bar_width_ms,
        marker_color=colors['generation'],
        customdata=df['month_str'],
        hovertemplate="<b>%{customdata}</b><br>Generation: %{y:,.1f} kWh<extra></extra>",
        text=[f"(Gen)<br>{format_value_for_bar(val)}" for val in df['total_supplied_generation']],
        textposition="inside",
        textfont={"color": "white", "size": 10}
    ))
    
    # Consumption
    fig.add_trace(go.Bar(
        x=df['x_consumption'],
        y=df['total_consumption'],
        name="Consumption",
        width=bar_width_ms,
        marker_color=colors['consumption'],
        customdata=df['month_str'],
        hovertemplate="<b>%{customdata}</b><br>Consumption: %{y:,.1f} kWh<extra></extra>",
        text=[f"(Con)<br>{format_value_for_bar(val)}" for val in df['total_consumption']],
        textposition="inside",
        textfont={"color": "white", "size": 10}
    ))
    
    # Matched Settlement
    fig.add_trace(go.Bar(
        x=df['x_settlement'],
        y=df['total_matched_settlement'],
        name="Matched Settlement",
        width=bar_width_ms,
        marker_color=colors['matched_settlement'],
        customdata=list(zip(df['month_str'], df['matched_settlement_pct'], df['matched_settlement_pct'])),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Matched Settlement: %{y:,.1f} kWh (%{customdata[1]:.1f}%)<br>"
            "Matched Replacement : %{customdata[2]:.1f}%<extra></extra>"
        ),
        text=[f"(Match)<br>{format_value_for_bar(val)}" for val in df['total_matched_settlement']],
        textposition="inside",
        textfont={"color": "white", "size": 9}
    ))
    
    # Settlement with Banking
    fig.add_trace(go.Bar(
        x=df['x_settlement'],
        y=df['total_settlement_with_banking'],
        name="Settlement with Banking",
        width=bar_width_ms,
        marker_color=colors['banking_settlement'],
        customdata=list(zip(df['month_str'], df['banking_settlement_pct'], df['replacement_pct'])),
        hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Settlement with Banking: %{y:,.1f} kWh (%{customdata[1]:.1f}%)<br>"
                "Total Replacement : %{customdata[2]:.1f}%<extra></extra>"
            ),
        text=[f"(Bank)<br>{format_value_for_bar(val)}" for val in df['total_settlement_with_banking']],
        textposition="inside",
        textfont={"color": "white", "size": 9}
    ))
    
    fig.update_layout(
        height=600,
        hovermode='closest',
        showlegend=True,
        barmode='stack',  # stack settlements
        margin={"t": 80, "l": 80},
        title={
            "text": "Generation, Consumption & Settlement Breakdown",
            "x": 0.5,
            "xanchor": "center"
        },
        legend={
            "orientation": "h",
            "yanchor": "top",
            "y": 0.98,
            "xanchor": "right",
            "x": 1
        },
        bargap=0.2,
    )
    
    fig.update_xaxes(
        title_text=f"📅 Month",
        tickvals=df['month'],
        ticktext=df['month'].dt.strftime('%b %Y'),
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)'
    )

    fig.update_yaxes(
        title_text="⚡ Energy (kWh)",
        showgrid=True,
        gridcolor='rgba(128,128,128,0.2)'
    )
    return fig

import logging
from typing import Optional


def plot_total_grid_vs_actual_cost_bar_chart(df: pd.DataFrame, client_name: Optional[str] = None):
    """Plot total grid vs actual cost bar chart aggregated by month."""
    if df.empty: return None
    
    # Ensure month is datetime
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df['month']):
        df['month'] = pd.to_datetime(df['month'], errors='coerce')
    
    # Aggregate by month
    monthly_summary = df.groupby('month').agg({
        'grid_cost': 'sum',
        'actual_cost': 'sum'
    }).reset_index()
    
    monthly_summary = monthly_summary.sort_values('month')
    monthly_summary['month_str'] = monthly_summary['month'].dt.strftime('%b %Y')
    
    fig = go.Figure()
    fig.add_trace(go.Bar(x=monthly_summary['month_str'], y=monthly_summary['grid_cost'], name='Grid Cost', marker_color='#dc3545'))
    fig.add_trace(go.Bar(x=monthly_summary['month_str'], y=monthly_summary['actual_cost'], name='Actual Cost', marker_color='#28a745'))
    
    fig.update_layout(
        title=f"Total Grid vs Actual Cost - {client_name}" if client_name else "Total Grid vs Actual Cost",
        barmode='group',
        xaxis_title="Month",
        yaxis_title="Cost (Rs.)",
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1}
    )
    return fig


# TOD slot information — slot names must match values in tod_daily_summary.tod_slot (uppercased)
SLOT_METADATA = {
    'NORMAL': {'color': '#3B9BA0', 'label': 'Normal'},
    'OFF-PEAK': {'color': '#214A86', 'label': 'Off-Peak'},
    'PEAK': {'color': '#f87171', 'label': 'Peak'},
}

def get_slot_color_map():
    """Returns a dictionary mapping slot names to colors."""
    return {slot: meta['color'] for slot, meta in SLOT_METADATA.items()}

def convert_dates_to_string(start_date, end_date):
    """Converts date/datetime objects to strings."""
    try:
        s = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date) # type: ignore
        e = end_date.strftime('%Y-%m-%d') if hasattr(end_date, 'strftime') else str(end_date) # type: ignore
        return s, e
    except:
        return str(start_date), str(end_date)


def plot_tod_generation_consumption_lines(
    df: pd.DataFrame,
    plant_display_name: str,
    start_date: str,
    end_date: Optional[str] = None,
    granularity: str = "daily",
    selected_slots: Optional[list] = None
):
    if df is None or df.empty:
        return None

    if granularity == "daily":
        date_column = 'date'
    elif granularity == "monthly":
        date_column = 'month'
    else:
        date_column = 'datetime'

    df = df.copy()
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df = df.dropna(subset=[date_column])

    if df.empty:
        return None

    # Normalize slot names for consistent color lookup
    if 'slot' in df.columns:
        df['slot'] = df['slot'].str.strip().str.upper()

    slot_colors = get_slot_color_map()
    fig = go.Figure()

    slots = df['slot'].unique() if 'slot' in df.columns else []
    slot_label = {k: v['label'] for k, v in SLOT_METADATA.items()}

    for slot in slots:
        slot_data = df[df['slot'] == slot].sort_values(date_column)
        color = slot_colors.get(slot, '#2E86AB')
        label = slot_label.get(slot, slot.title())

        # Generation — solid line per slot
        fig.add_trace(go.Scatter(
            x=slot_data[date_column],
            y=slot_data['generation_kwh'],
            mode='lines+markers',
            name="Generation",
            line={"color": color, "width": 2.5},
            marker={"symbol": "circle", "size": 5},
            legendgroup=slot,
            legendgrouptitle={"text": label},
        ))

        # Consumption — dashed line per slot (same color)
        fig.add_trace(go.Scatter(
            x=slot_data[date_column],
            y=slot_data['consumption_kwh'],
            mode='lines+markers',
            name="Consumption",
            line={"color": color, "width": 2.5, "dash": "dash"},
            marker={"symbol": "diamond", "size": 5},
            legendgroup=slot,
        ))

    title_map = {"daily": "Daily", "60min": "Hourly", "monthly": "Monthly"}
    date_range_str = start_date if start_date == end_date else f"{start_date} to {end_date}"

    fig.update_layout(
        title=f"📊 ToD Generation vs Consumption ({title_map.get(granularity, granularity)}) - {plant_display_name} ({date_range_str})",
        xaxis_title="📅 Date",
        yaxis_title="⚡ Energy (kWh)",
        template="plotly_white",
        height=600,
        legend={
            "orientation": "v",
            "yanchor": "top",
            "y": 1,
            "xanchor": "left",
            "x": 1.02,
            "groupclick": "toggleitem",
        },
        margin={"r": 160},
    )

    # Set x-axis tick format to suppress time component
    if granularity == "monthly":
        fig.update_xaxes(tickformat="%b %Y", dtick="M1")
    elif granularity == "daily":
        fig.update_xaxes(tickformat="%d %b %Y")
    # 60min: leave default (shows datetime naturally)

    return fig
