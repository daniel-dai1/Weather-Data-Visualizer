import os # For checking if the default CSV file exists
import pandas as pd # For data manipulation
import plotly.express as px # For interactive visualizations
import streamlit as st # For building the web app

# ==========================================
# 1. PAGE CONFIG & DARK THEME SETUP
# ==========================================
st.set_page_config(
    page_title="Climate Visualizer", layout="wide", initial_sidebar_state="expanded"
)

# Dark theme color variables
bg_color = "#1E1E1E"
card_bg = "#2D2D2D"
text_color = "#F5F5F7"
subtext_color = "#A1A1A6"
border_color = "#3A3A3C"
chart_grid = "#3A3A3C"
accent_color = "#2997FF"
btn_bg = "#3A3A3C"
btn_text = "#FFFFFF"

# Inject custom Dark Mode CSS
st.markdown(
    f"""
    <style>
        /* Main background & typography */
        [data-testid="stAppViewContainer"] {{
            background-color: {bg_color};
            color: {text_color};
            font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}

        /* Headers & general text */
        h1, h2, h3, h4, p, span {{
            color: {text_color} !important;
        }}

        /* Sidebar styling */
        [data-testid="stSidebar"] {{
            background-color: {card_bg};
            border-right: 1px solid {border_color};
        }}

        /* Custom Cards */
        .apple-card {{
            background-color: {card_bg};
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
            margin-bottom: 1.2rem;
            border: 1px solid {border_color};
        }}

        /* Metric Styling */
        [data-testid="stMetricValue"] {{
            font-size: 2rem;
            font-weight: 700;
            color: {text_color} !important;
        }}
        [data-testid="stMetricLabel"] {{
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.08rem;
            color: {subtext_color} !important;
        }}

        /* Date range input contrast */
        [data-testid="stDateInputField"] span {{
            color: #31333F !important;
            -webkit-text-fill-color: #31333F !important;
        }}

        /* File Uploader Visibility */
        [data-testid="stFileUploader"] section {{
            background-color: {card_bg} !important;
            border: 1px dashed {border_color} !important;
            border-radius: 12px;
            color: {text_color} !important;
        }}
        [data-testid="stFileUploader"] section button {{
            background-color: {btn_bg} !important;
            color: {btn_text} !important;
            border: 1px solid {border_color} !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }}
        [data-testid="stFileUploaderDropzoneInstructions"] span {{
            color: {subtext_color} !important;
        }}

        /* Hide Streamlit Clutter */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        [data-testid="stHeader"] {{background: rgba(0,0,0,0);}}
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. MAIN HEADER & DATA INGESTION
# ==========================================

st.markdown('<div class="apple-card">', unsafe_allow_html=True) # Custom card for header
st.title("Hourly Climate Visualizer")
st.write(
    "Analyze climate trends dynamically. Upload a custom dataset or view the default sample."
)
st.markdown("</div>", unsafe_allow_html=True)

# File Uploader Widget
uploaded_file = st.file_uploader(
    "Upload an Environment Canada Hourly Climate CSV File", type=["csv"]
)

# Data Loading Logic: Use uploaded file if present; otherwise fall back to local default file
df_raw = None # Initialize raw DataFrame
data_source_label = ""
default_filename = "en_climate_daily_ON_6158776_1971_P1D.csv"

if uploaded_file is not None: # If user uploads a file, read it
    df_raw = pd.read_csv(uploaded_file)
    data_source_label = f"Uploaded File ({uploaded_file.name})"
elif os.path.exists(default_filename): # If no upload, check for default file in project directory
    df_raw = pd.read_csv(default_filename)
    data_source_label = f"Default Sample Dataset ({default_filename})"

# ==========================================
# 3. PROCESSING & VISUALIZATION
# ==========================================

if df_raw is not None: # If we have a DataFrame (either from upload or default), proceed with processing
    # Clean Column Names
    df_raw.columns = df_raw.columns.str.strip()

    # Locate Date Column
    date_col = next(
        (col for col in df_raw.columns if "date" in col.lower()), None
    )
    if date_col:
        df_raw[date_col] = pd.to_datetime(df_raw[date_col])

    # Identify Numeric Columns
    numeric_cols = [
        col
        for col in df_raw.columns
        if any(kw in col.lower() for kw in ["temp", "precip", "spd", "humidity"])
    ]

    if numeric_cols:
        # Clean numeric data & interpolate small gaps
        for col in numeric_cols:
            df_raw[col] = pd.to_numeric(df_raw[col], errors="coerce")

        df_clean = df_raw.copy()
        df_clean[numeric_cols] = df_clean[numeric_cols].interpolate(
            method="linear", limit=3
        )

        # Sidebar Filtering
        st.sidebar.header("Data Filter")
        st.sidebar.caption(f"Currently Showing: **{data_source_label}**")

        selected_metric = st.sidebar.selectbox("Weather Metric", numeric_cols)

        if date_col: # If a date column exists, provide a date range filter
            min_date = df_clean[date_col].min().date()
            max_date = df_clean[date_col].max().date()

            start_date, end_date = st.sidebar.date_input(
                "Date Range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

            mask = (df_clean[date_col].dt.date >= start_date) & (
                df_clean[date_col].dt.date <= end_date
            )
            filtered_df = df_clean.loc[mask]
        else:
            filtered_df = df_clean

        # Summary Cards
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        st.subheader(f"Summary Statistics: {selected_metric}")
        col1, col2, col3 = st.columns(3)
        col1.metric("Average", f"{filtered_df[selected_metric].mean():.1f}")
        col2.metric("Max", f"{filtered_df[selected_metric].max():.1f}")
        col3.metric("Min", f"{filtered_df[selected_metric].min():.1f}")
        st.markdown("</div>", unsafe_allow_html=True)

        # Interactive Chart Card
        st.markdown('<div class="apple-card">', unsafe_allow_html=True)
        st.subheader(f"Interactive Trend: {selected_metric}")

        if date_col: # If a date column exists, plot the metric over time
            fig = px.line( # Create line chart with date on x-axis and selected metric on y-axis
                filtered_df,
                x=date_col,
                y=selected_metric,
                color_discrete_sequence=[accent_color],
            )
            fig.update_layout( # Update layout for dark theme
                plot_bgcolor=card_bg,
                paper_bgcolor=card_bg,
                font=dict(color=text_color),
                xaxis_title=None,
                yaxis_title=None,
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor=chart_grid),
                margin=dict(l=0, r=0, t=20, b=0),
                height=450,
            )
        else: # If no date column, plot the metric as a simple line chart without x-axis
            fig = px.line(
                filtered_df, y=selected_metric, color_discrete_sequence=[accent_color]
            )

        st.plotly_chart( # Render the Plotly chart in Streamlit with container width and no mode bar
            fig, use_container_width=True, config={"displayModeBar": False}
        )
        st.markdown("</div>", unsafe_allow_html=True) # Close the interactive chart card

    else: # If no numeric columns are found, display a warning message
        st.warning(
            "Could not automatically identify numeric weather columns in this CSV file."
        )

else: # If no DataFrame is loaded (neither uploaded nor default), display an info message prompting the user to upload a file or use the default
    # Fallback message
    st.info(
        f"Please upload a CSV file above, or save a file named '{default_filename}' in the project folder to auto-load sample data."
    )