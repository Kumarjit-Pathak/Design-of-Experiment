"""
Data Explorer Page

Interactive exploration of the e-commerce dataset including:
- Summary statistics
- Feature distributions
- Missing data analysis
- Correlation analysis

Author: DOE Simulator Team
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.utils.data_loader import load_data, identify_column_types

# Page config
st.set_page_config(page_title="Data Explorer", page_icon="📊", layout="wide")

# Custom CSS - SLATE PROFESSIONAL THEME
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: #cbd5e1;
    }

    h1, h2, h3 {
        color: #38bdf8;
    }

    h4, h5, h6 {
        color: #facc15;
    }

    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }

    /* Fix sidebar navigation text visibility */
    [data-testid="stSidebar"] .css-1544g2n,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] a:hover {
        color: #38bdf8 !important;
    }

    [data-testid="stMetricValue"] {
        color: #38bdf8;
        font-weight: bold;
        font-size: 1.8rem;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .stButton>button {
        background-color: #38bdf8;
        color: #1e293b;
        font-weight: bold;
        border: 2px solid #38bdf8;
        border-radius: 6px;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #facc15;
        border-color: #facc15;
        box-shadow: 0 0 20px rgba(250, 204, 21, 0.5);
        transform: translateY(-2px);
    }

    .metric-card {
        background-color: #334155;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #38bdf8;
        text-align: center;
    }

    .stTabs [data-baseweb="tab"] {
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        color: #38bdf8;
        border-bottom-color: #38bdf8;
    }

    p, li, span {
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("📊 Data Explorer")
st.markdown("Explore the e-commerce customer dataset with 20,000 observations and 24 features.")

# Load data with caching
@st.cache_data
def load_ecommerce_data():
    """Load and cache the e-commerce dataset."""
    data_path = os.path.join("data", "raw", "ecommerce_data.csv")
    try:
        df = pd.read_csv(data_path)
        return df
    except FileNotFoundError:
        st.error("Dataset not found! Please ensure 'data/raw/ecommerce_data.csv' exists.")
        return None

# Load data
df = load_ecommerce_data()

if df is not None:
    # Sidebar filters
    st.sidebar.header("🔍 Filters")

    # Filter by income level
    income_levels = ['All'] + sorted(df['income_level'].unique().tolist())
    selected_income = st.sidebar.selectbox("Income Level", income_levels)

    # Filter by location
    locations = ['All'] + sorted(df['location'].unique().tolist())
    selected_location = st.sidebar.selectbox("Location", locations)

    # Filter by gender
    genders = ['All'] + sorted(df['gender'].unique().tolist())
    selected_gender = st.sidebar.selectbox("Gender", genders)

    # Apply filters
    filtered_df = df.copy()
    if selected_income != 'All':
        filtered_df = filtered_df[filtered_df['income_level'] == selected_income]
    if selected_location != 'All':
        filtered_df = filtered_df[filtered_df['location'] == selected_location]
    if selected_gender != 'All':
        filtered_df = filtered_df[filtered_df['gender'] == selected_gender]

    # Display filter results
    if len(filtered_df) < len(df):
        st.info(f"Filtered: {len(filtered_df):,} observations (from {len(df):,} total)")

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "📊 Distributions", "🔗 Correlations", "❓ Missing Data"])

    # TAB 1: Overview
    with tab1:
        st.header("Dataset Overview")

        # Key metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Observations", f"{len(filtered_df):,}")

        with col2:
            st.metric("Total Features", len(filtered_df.columns))

        with col3:
            completeness = (1 - filtered_df.isnull().sum().sum() / (len(filtered_df) * len(filtered_df.columns))) * 100
            st.metric("Completeness", f"{completeness:.1f}%")

        with col4:
            memory_mb = filtered_df.memory_usage(deep=True).sum() / (1024**2)
            st.metric("Memory Usage", f"{memory_mb:.1f} MB")

        st.markdown("---")

        # Feature categories
        st.subheader("Feature Categories")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
            **Demographics (5)**
            - customer_id, age, gender, location, income_level, education

            **Shopping Behavior (5)**
            - account_age_days, total_orders, avg_order_value, last_order_days_ago, product_category_preference

            **Engagement Metrics (5)**
            - email_open_rate, website_visits_per_month, mobile_app_user, loyalty_program_member, customer_service_interactions
            """)

        with col2:
            st.markdown("""
            **Behavioral Indicators (4)**
            - cart_abandonment_rate, review_count, avg_rating_given, social_media_follower

            **Target Variables (4)**
            - conversion_rate, lifetime_value, churn_probability, response_to_marketing
            """)

        st.markdown("---")

        # Summary statistics for key variables
        st.subheader("Key Statistics")

        key_vars = ['age', 'total_orders', 'avg_order_value', 'conversion_rate', 'lifetime_value']
        summary_stats = filtered_df[key_vars].describe().T
        summary_stats['missing'] = filtered_df[key_vars].isnull().sum()
        summary_stats['missing_pct'] = (summary_stats['missing'] / len(filtered_df) * 100).round(2)

        st.dataframe(summary_stats.style.format("{:.2f}"), use_container_width=True)

        st.markdown("---")

        # Sample data
        st.subheader("Sample Data (First 10 Rows)")
        st.dataframe(filtered_df.head(10), use_container_width=True)

    # TAB 2: Distributions
    with tab2:
        st.header("Feature Distributions")

        # Select variable
        numerical_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = filtered_df.select_dtypes(include=['object']).columns.tolist()

        col1, col2 = st.columns([1, 2])

        with col1:
            var_type = st.radio("Variable Type", ["Numerical", "Categorical"])

            if var_type == "Numerical":
                selected_var = st.selectbox("Select Variable", numerical_cols)
            else:
                selected_var = st.selectbox("Select Variable", categorical_cols)

        with col2:
            if var_type == "Numerical":
                # Histogram
                fig = px.histogram(
                    filtered_df,
                    x=selected_var,
                    nbins=50,
                    title=f"Distribution of {selected_var}",
                    labels={selected_var: selected_var.replace('_', ' ').title()},
                    color_discrete_sequence=['#667eea']
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Box plot
                fig2 = px.box(
                    filtered_df,
                    y=selected_var,
                    title=f"Box Plot of {selected_var}",
                    labels={selected_var: selected_var.replace('_', ' ').title()},
                    color_discrete_sequence=['#764ba2']
                )
                fig2.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig2, use_container_width=True)

            else:
                # Bar chart for categorical
                value_counts = filtered_df[selected_var].value_counts()
                fig = px.bar(
                    x=value_counts.index,
                    y=value_counts.values,
                    title=f"Distribution of {selected_var}",
                    labels={'x': selected_var.replace('_', ' ').title(), 'y': 'Count'},
                    color=value_counts.values,
                    color_continuous_scale='Purples'
                )
                fig.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig, use_container_width=True)

                # Pie chart
                fig2 = px.pie(
                    values=value_counts.values,
                    names=value_counts.index,
                    title=f"Proportion of {selected_var}",
                    color_discrete_sequence=px.colors.sequential.Purples
                )
                fig2.update_layout(height=400)
                st.plotly_chart(fig2, use_container_width=True)

    # TAB 3: Correlations
    with tab3:
        st.header("Correlation Analysis")

        # Select variables for correlation
        st.markdown("Select variables to analyze correlations:")

        numerical_cols = filtered_df.select_dtypes(include=[np.number]).columns.tolist()

        # Default selection
        default_vars = ['age', 'total_orders', 'avg_order_value', 'conversion_rate', 'lifetime_value', 'churn_probability']
        default_vars = [v for v in default_vars if v in numerical_cols]

        selected_vars = st.multiselect(
            "Select Variables",
            numerical_cols,
            default=default_vars
        )

        if len(selected_vars) >= 2:
            # Calculate correlation
            corr_matrix = filtered_df[selected_vars].corr()

            # Heatmap
            fig = px.imshow(
                corr_matrix,
                title="Correlation Matrix",
                labels=dict(color="Correlation"),
                x=selected_vars,
                y=selected_vars,
                color_continuous_scale='RdBu_r',
                zmin=-1,
                zmax=1
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True)

            # Highlight strong correlations
            st.subheader("Strong Correlations (|r| > 0.5)")

            strong_corr = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i+1, len(corr_matrix.columns)):
                    if abs(corr_matrix.iloc[i, j]) > 0.5:
                        strong_corr.append({
                            'Variable 1': corr_matrix.columns[i],
                            'Variable 2': corr_matrix.columns[j],
                            'Correlation': corr_matrix.iloc[i, j]
                        })

            if strong_corr:
                strong_corr_df = pd.DataFrame(strong_corr)
                strong_corr_df = strong_corr_df.sort_values('Correlation', key=abs, ascending=False)
                st.dataframe(strong_corr_df.style.format({'Correlation': '{:.3f}'}), use_container_width=True)
            else:
                st.info("No strong correlations (|r| > 0.5) found among selected variables.")

        else:
            st.warning("Please select at least 2 variables for correlation analysis.")

    # TAB 4: Missing Data
    with tab4:
        st.header("Missing Data Analysis")

        # Calculate missing data
        missing_counts = filtered_df.isnull().sum()
        missing_pct = (missing_counts / len(filtered_df) * 100).round(2)

        missing_df = pd.DataFrame({
            'Feature': missing_counts.index,
            'Missing Count': missing_counts.values,
            'Missing %': missing_pct.values
        })

        # Only show features with missing data
        missing_df = missing_df[missing_df['Missing Count'] > 0].sort_values('Missing Count', ascending=False)

        if not missing_df.empty:
            # Bar chart
            fig = px.bar(
                missing_df,
                x='Feature',
                y='Missing %',
                title="Missing Data by Feature",
                labels={'Missing %': 'Missing (%)', 'Feature': 'Feature'},
                color='Missing %',
                color_continuous_scale='Reds'
            )
            fig.update_layout(height=400, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Table
            st.subheader("Missing Data Details")
            st.dataframe(missing_df, use_container_width=True)

            # Summary
            total_missing = missing_counts.sum()
            total_cells = len(filtered_df) * len(filtered_df.columns)
            overall_completeness = (1 - total_missing / total_cells) * 100

            st.success(f"Overall Data Completeness: {overall_completeness:.2f}%")

        else:
            st.success("✅ No missing data found in the filtered dataset!")

else:
    st.error("Failed to load dataset. Please check the data file path.")
