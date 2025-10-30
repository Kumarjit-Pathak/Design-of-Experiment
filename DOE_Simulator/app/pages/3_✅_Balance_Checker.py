"""
Balance Checker Page

Check balance between treatment and control groups on baseline covariates.
This is CRITICAL for validating experimental designs before analyzing treatment effects.

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

from src.diagnostics.balance_checker import BalanceChecker

# Page config
st.set_page_config(page_title="Balance Checker", page_icon="✅", layout="wide")

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

    p, li, span {
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("✅ Balance Checker")
st.markdown("""
Check if treatment and control groups are balanced on baseline covariates.
**This is essential before analyzing treatment effects!**
""")

# Load data
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('../data/raw/ecommerce_data.csv')
        return df
    except:
        st.error("Dataset not found!")
        return None

df = load_data()

if df is not None:
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")

    # Step 1: Create or load treatment assignment
    st.sidebar.subheader("1️⃣ Treatment Assignment")

    st.sidebar.info("📌 Treatment is assigned based on Customer ID for proper randomization")

    assignment_method = st.sidebar.radio(
        "Assignment Method",
        ["Random Assignment (by Customer ID)", "Use Pre-Assigned Column"]
    )

    if assignment_method == "Random Assignment (by Customer ID)":
        treatment_ratio = st.sidebar.slider(
            "Treatment Group Size (%)",
            min_value=10,
            max_value=90,
            value=50
        )

        random_seed_treatment = st.sidebar.number_input(
            "Random Seed",
            min_value=0,
            max_value=9999,
            value=42
        )

        if st.sidebar.button("🎲 Assign Treatment", type="primary"):
            # Use customer_id for randomization (if available)
            if 'customer_id' in df.columns:
                # Create reproducible randomization based on customer_id hash
                np.random.seed(random_seed_treatment)

                # Randomly shuffle customer indices
                shuffled_indices = np.random.permutation(len(df))

                # Assign treatment based on shuffled order
                n_treatment = int(len(df) * treatment_ratio / 100)
                treatment_assignment = np.zeros(len(df), dtype=int)
                treatment_assignment[shuffled_indices[:n_treatment]] = 1

                df['treatment_group'] = treatment_assignment

            else:
                # Fallback to simple random assignment by row index
                np.random.seed(random_seed_treatment)
                n_treatment = int(len(df) * treatment_ratio / 100)

                treatment_assignment = np.array([1] * n_treatment + [0] * (len(df) - n_treatment))
                np.random.shuffle(treatment_assignment)

                df['treatment_group'] = treatment_assignment

            st.session_state['data_with_treatment'] = df
            st.sidebar.success(f"✅ Treatment assigned: {(df['treatment_group']==1).sum():,} treatment, {(df['treatment_group']==0).sum():,} control")

    else:
        # Only allow selecting identifier columns or pre-assigned treatment columns
        identifier_cols = ['customer_id', 'treatment_group', 'treatment', 'group', 'assignment']
        available_cols = [col for col in df.columns if col in identifier_cols]

        if not available_cols:
            st.sidebar.warning("No pre-assigned treatment columns found. Use 'Random Assignment' instead.")
        else:
            existing_col = st.sidebar.selectbox(
                "Select Treatment Column",
                available_cols
            )

            # Convert to binary 0/1 if needed
            unique_vals = df[existing_col].unique()
            if len(unique_vals) == 2:
                # Map to 0 and 1
                val_map = {unique_vals[0]: 0, unique_vals[1]: 1}
                df['treatment_group'] = df[existing_col].map(val_map)
                st.session_state['data_with_treatment'] = df
                st.sidebar.success(f"✅ Using column: {existing_col}")
            else:
                st.sidebar.error(f"Column {existing_col} must have exactly 2 unique values")

    # Step 2: Select covariates to check
    st.sidebar.subheader("2️⃣ Select Covariates")

    # Issue #2 FIX: Use covariates from Sampling Methods if available
    if 'balance_covariates' in st.session_state and st.session_state['balance_covariates']:
        default_covariates = [col for col in st.session_state['balance_covariates'] if col in df.columns]
    else:
        default_covariates = [
            'age', 'gender', 'location', 'income_level',
            'total_orders', 'avg_order_value',
            'email_open_rate', 'loyalty_program_member'
        ]
        default_covariates = [col for col in default_covariates if col in df.columns]

    selected_covariates = st.sidebar.multiselect(
        "Covariates to Check",
        [col for col in df.columns if col not in ['customer_id', 'treatment_group', 'treatment_label']],
        default=default_covariates,
        help="These were pre-selected from your Sampling Methods configuration. You can modify them."
    )

    # Step 3: Settings
    st.sidebar.subheader("3️⃣ Settings")

    smd_threshold = st.sidebar.slider(
        "SMD Threshold for Balance",
        min_value=0.05,
        max_value=0.30,
        value=0.10,
        step=0.05,
        help="Standardized Mean Difference threshold. |SMD| < threshold indicates balance."
    )

    perform_tests = st.sidebar.checkbox("Perform Statistical Tests", value=True)

    # Issue #2 FIX: Auto-run balance check if triggered from Sampling Methods
    auto_run = st.session_state.get('auto_run_balance_check', False)

    # Run balance check button (or auto-run)
    run_check = st.sidebar.button("✅ Check Balance", type="primary") or auto_run

    # Clear auto-run flag after first use
    if auto_run:
        st.session_state['auto_run_balance_check'] = False
        st.info("🎯 **Auto-loaded from Sampling Methods page!** Results populated with your selected balance variables.")

    # Main content
    st.markdown("---")

    if 'data_with_treatment' in st.session_state:
        data_to_check = st.session_state['data_with_treatment']

        # Display treatment distribution
        st.subheader("Treatment Group Distribution")

        treatment_counts = data_to_check['treatment_group'].value_counts()

        col1, col2, col3 = st.columns(3)

        with col1:
            total_n = len(data_to_check)
            st.metric("Total Observations", f"{total_n:,}")

        with col2:
            control_n = (data_to_check['treatment_group'] == 0).sum()
            st.metric("Control Group", f"{control_n:,}")

        with col3:
            treatment_n = (data_to_check['treatment_group'] == 1).sum()
            st.metric("Treatment Group", f"{treatment_n:,}")

        # Pie chart
        fig = go.Figure(data=[go.Pie(
            labels=['Control (0)', 'Treatment (1)'],
            values=[control_n, treatment_n],
            hole=0.3,
            marker_colors=['#667eea', '#764ba2']
        )])
        fig.update_layout(title="Treatment Assignment", height=300)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Run balance check
        if run_check and len(selected_covariates) > 0:
            with st.spinner("Checking balance..."):
                checker = BalanceChecker(
                    data=data_to_check,
                    treatment_col='treatment_group',
                    group_labels={0: 'Control', 1: 'Treatment'}
                )

                results = checker.check_balance(
                    covariates=selected_covariates,
                    threshold_smd=smd_threshold,
                    perform_tests=perform_tests
                )

            # Overall balance score
            st.header("📊 Overall Balance Assessment")

            overall = results['overall_balance']

            # Color-coded metric
            if overall['status'] == 'EXCELLENT':
                color = '🟢'
            elif overall['status'] == 'GOOD':
                color = '🟡'
            elif overall['status'] == 'ACCEPTABLE':
                color = '🟠'
            else:
                color = '🔴'

            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Balance Score", f"{overall['balance_percentage']:.1f}%")

            with col2:
                st.metric("Status", f"{color} {overall['status']}")

            with col3:
                st.metric("Balanced Covariates", f"{overall['n_balanced']}/{overall['n_covariates']}")

            # Recommendation
            if overall['status'] in ['EXCELLENT', 'GOOD']:
                st.success(f"✅ {overall['recommendation']}")
            elif overall['status'] == 'ACCEPTABLE':
                st.warning(f"⚠️ {overall['recommendation']}")
            else:
                st.error(f"❌ {overall['recommendation']}")

            st.markdown("---")

            # Issue #3 FIX: Display statistical test results prominently
            if perform_tests:
                st.markdown("---")
                st.header("📊 Statistical Test Results")

                # Collect all test results
                numerical_tests = []
                categorical_tests = []

                for result in results['balance_results']:
                    if result['type'] == 'numerical' and 'p_value' in result:
                        numerical_tests.append({
                            'Covariate': result['covariate'],
                            'Test': result.get('test_name', 't-test'),
                            't-statistic': result.get('test_statistic', 'N/A'),
                            'p-value': result.get('p_value', 'N/A'),
                            'Significant': '❌ Yes' if result.get('significant', False) else '✅ No',
                            'Interpretation': 'Groups differ' if result.get('significant', False) else 'Groups similar'
                        })
                    elif result['type'] == 'categorical' and 'p_value' in result:
                        categorical_tests.append({
                            'Covariate': result['covariate'],
                            'Test': 'Chi-square',
                            'χ² statistic': result.get('chi_square', 'N/A'),
                            'p-value': result.get('p_value', 'N/A'),
                            "Cramér's V": result.get('cramers_v', 'N/A'),
                            'Significant': '❌ Yes' if result.get('significant', False) else '✅ No',
                            'Interpretation': 'Distributions differ' if result.get('significant', False) else 'Distributions similar'
                        })

                # Display numerical tests
                if numerical_tests:
                    st.subheader("🔢 Numerical Variables: t-tests")
                    numerical_df = pd.DataFrame(numerical_tests)

                    st.dataframe(
                        numerical_df,
                        use_container_width=True,
                        column_config={
                            "t-statistic": st.column_config.NumberColumn("t-statistic", format="%.4f"),
                            "p-value": st.column_config.NumberColumn("p-value", format="%.4f")
                        }
                    )

                    # Summary
                    n_significant = sum(1 for t in numerical_tests if '❌' in t['Significant'])
                    if n_significant == 0:
                        st.success(f"✅ All {len(numerical_tests)} numerical variables show no significant differences (good for balance!)")
                    else:
                        st.warning(f"⚠️ {n_significant} of {len(numerical_tests)} numerical variables show significant differences")

                # Display categorical tests
                if categorical_tests:
                    st.subheader("📁 Categorical Variables: Chi-square tests")
                    categorical_df = pd.DataFrame(categorical_tests)

                    st.dataframe(
                        categorical_df,
                        use_container_width=True,
                        column_config={
                            "χ² statistic": st.column_config.NumberColumn("χ² statistic", format="%.4f"),
                            "p-value": st.column_config.NumberColumn("p-value", format="%.4f"),
                            "Cramér's V": st.column_config.NumberColumn("Cramér's V", format="%.4f")
                        }
                    )

                    # Summary
                    n_significant = sum(1 for t in categorical_tests if '❌' in t['Significant'])
                    if n_significant == 0:
                        st.success(f"✅ All {len(categorical_tests)} categorical variables show no significant differences")
                    else:
                        st.warning(f"⚠️ {n_significant} of {len(categorical_tests)} categorical variables show significant differences")

                st.info("💡 **Note:** Non-significant p-values (p > 0.05) indicate good balance. However, focus on effect sizes (SMD) rather than p-values for balance assessment.")

            # Covariate-level results
            st.markdown("---")
            st.header("📋 Covariate-Level Balance")

            # Create tabs for different views
            tab1, tab2, tab3 = st.tabs(["📊 Summary Table", "📈 Love Plot Data", "🔍 Detailed Results"])

            with tab1:
                # Summary table
                summary_data = []

                for result in results['balance_results']:
                    if result['type'] == 'numerical':
                        summary_data.append({
                            'Covariate': result['covariate'],
                            'Type': 'Numerical',
                            'SMD': result.get('standardized_mean_difference', np.nan),
                            '|SMD|': result.get('abs_smd', np.nan),
                            'Balanced': '✅' if result['balanced'] else '❌',
                            'Status': result['interpretation']
                        })
                    else:
                        summary_data.append({
                            'Covariate': result['covariate'],
                            'Type': 'Categorical',
                            'SMD': 'N/A',
                            '|SMD|': 'N/A',
                            'Balanced': '✅' if result['balanced'] else '❌',
                            'Status': result.get('interpretation', 'Check distributions')
                        })

                summary_df = pd.DataFrame(summary_data)

                # Apply color coding
                def color_balance(val):
                    if val == '✅':
                        return 'background-color: #d4edda'
                    elif val == '❌':
                        return 'background-color: #f8d7da'
                    return ''

                styled_df = summary_df.style.applymap(
                    color_balance,
                    subset=['Balanced']
                ).format({
                    'SMD': lambda x: f'{x:.4f}' if isinstance(x, (int, float)) else x,
                    '|SMD|': lambda x: f'{x:.4f}' if isinstance(x, (int, float)) else x
                })

                st.dataframe(styled_df, use_container_width=True)

            with tab2:
                # Love plot data
                st.subheader("Love Plot Data")
                st.markdown("""
                **Love plots** visualize standardized mean differences (SMD) for all covariates.
                Points closer to zero indicate better balance.

                **Reference thresholds:**
                - 🟢 |SMD| < 0.1: Excellent balance
                - 🟡 |SMD| < 0.2: Good balance
                - 🟠 |SMD| < 0.3: Acceptable balance
                - 🔴 |SMD| ≥ 0.3: Poor balance
                """)

                love_data = results['love_plot_data']

                if not love_data.empty:
                    # Create Enhanced Love plot with better interactivity
                    fig = go.Figure()

                    # Map colors
                    colors = love_data['color'].map({
                        'green': '#4ade80',   # Bright green for excellent
                        'yellow': '#facc15',  # Yellow for good
                        'orange': '#fb923c',  # Orange for acceptable
                        'red': '#ef4444'      # Red for poor
                    })

                    # Create hover text with interpretations
                    hover_text = []
                    for idx, row in love_data.iterrows():
                        interpretation = "Excellent" if row['abs_smd'] < 0.1 else \
                                       "Good" if row['abs_smd'] < 0.2 else \
                                       "Acceptable" if row['abs_smd'] < 0.3 else "Poor"
                        hover_text.append(
                            f"<b>{row['covariate']}</b><br>" +
                            f"SMD: {row['smd']:.4f}<br>" +
                            f"|SMD|: {row['abs_smd']:.4f}<br>" +
                            f"Balance: {interpretation}<br>" +
                            "<extra></extra>"
                        )

                    # Add bars with custom hover
                    fig.add_trace(go.Bar(
                        y=love_data['covariate'],
                        x=love_data['smd'],
                        orientation='h',
                        marker=dict(
                            color=colors,
                            line=dict(color='#1e293b', width=1)
                        ),
                        text=love_data['smd'].apply(lambda x: f'{x:.3f}'),
                        textposition='outside',
                        textfont=dict(size=11, color='#cbd5e1'),
                        name='SMD',
                        hovertemplate=hover_text,
                        hoverlabel=dict(
                            bgcolor='#334155',
                            font_size=12,
                            font_family="monospace"
                        )
                    ))

                    # Add reference lines with annotations
                    max_abs = love_data['abs_smd'].max()
                    x_range = max(0.5, max_abs * 1.15)

                    # Zero line (perfect balance)
                    fig.add_vline(
                        x=0,
                        line_color="#cbd5e1",
                        line_width=2,
                        opacity=0.8
                    )

                    # Threshold lines
                    fig.add_vrect(
                        x0=-0.1, x1=0.1,
                        fillcolor="#4ade80",
                        opacity=0.1,
                        layer="below",
                        line_width=0,
                        annotation_text="Excellent",
                        annotation_position="top left"
                    )

                    fig.add_vline(x=-0.1, line_dash="dash", line_color="#94a3b8", opacity=0.4)
                    fig.add_vline(x=0.1, line_dash="dash", line_color="#94a3b8", opacity=0.4)

                    if max_abs > 0.2:
                        fig.add_vline(x=-0.2, line_dash="dash", line_color="#facc15", opacity=0.4)
                        fig.add_vline(x=0.2, line_dash="dash", line_color="#facc15", opacity=0.4)

                    if max_abs > 0.3:
                        fig.add_vline(x=-0.3, line_dash="dash", line_color="#ef4444", opacity=0.4)
                        fig.add_vline(x=0.3, line_dash="dash", line_color="#ef4444", opacity=0.4)

                    fig.update_layout(
                        title={
                            'text': "Love Plot: Standardized Mean Differences",
                            'x': 0.5,
                            'xanchor': 'center',
                            'font': {'size': 18, 'color': '#38bdf8'}
                        },
                        xaxis_title="Standardized Mean Difference (SMD)",
                        yaxis_title="Covariate",
                        height=max(500, len(love_data) * 45),
                        showlegend=False,
                        xaxis=dict(
                            range=[-x_range, x_range],
                            gridcolor='#334155',
                            zerolinecolor='#cbd5e1'
                        ),
                        yaxis=dict(
                            gridcolor='#334155'
                        ),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(30, 41, 59, 0.5)',
                        font=dict(color='#cbd5e1', size=12),
                        hovermode='closest'
                    )

                    st.plotly_chart(fig, use_container_width=True)

                    # Add interactive threshold selector
                    st.markdown("---")
                    st.markdown("**🎯 Balance Threshold Explorer**")

                    selected_threshold = st.select_slider(
                        "Select SMD Threshold",
                        options=[0.05, 0.10, 0.15, 0.20, 0.25, 0.30],
                        value=0.10,
                        help="Variables with |SMD| below this threshold are considered balanced"
                    )

                    n_balanced_at_threshold = (love_data['abs_smd'] < selected_threshold).sum()
                    balance_pct = (n_balanced_at_threshold / len(love_data) * 100)

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric(
                            "Threshold",
                            f"{selected_threshold:.2f}",
                            delta="Stricter" if selected_threshold < 0.10 else "More lenient"
                        )

                    with col2:
                        st.metric(
                            "Balanced Variables",
                            f"{n_balanced_at_threshold}/{len(love_data)}",
                            delta=f"{balance_pct:.0f}%"
                        )

                    with col3:
                        if balance_pct >= 90:
                            status = "🟢 Excellent"
                        elif balance_pct >= 70:
                            status = "🟡 Good"
                        elif balance_pct >= 50:
                            status = "🟠 Fair"
                        else:
                            status = "🔴 Poor"
                        st.metric("Balance Quality", status)

                    # Display data table with color coding
                    st.markdown("---")
                    st.markdown("**📊 Detailed Balance Table**")

                    # Add interpretation column
                    love_data_display = love_data.copy()
                    love_data_display['balance_status'] = love_data_display['abs_smd'].apply(
                        lambda x: '🟢 Excellent' if x < 0.1 else
                                 '🟡 Good' if x < 0.2 else
                                 '🟠 Acceptable' if x < 0.3 else
                                 '🔴 Poor'
                    )

                    st.dataframe(
                        love_data_display[['covariate', 'smd', 'abs_smd', 'balance_status']],
                        use_container_width=True,
                        column_config={
                            "covariate": "Covariate",
                            "smd": st.column_config.NumberColumn("SMD", format="%.4f"),
                            "abs_smd": st.column_config.NumberColumn("|SMD|", format="%.4f"),
                            "balance_status": "Balance Status"
                        }
                    )

                else:
                    st.info("No numerical variables in the balance check. Love plot requires numerical covariates.")

            with tab3:
                # Detailed results
                st.subheader("Detailed Covariate Results")

                for result in results['balance_results']:
                    with st.expander(f"{result['covariate']} ({result['type']})"):
                        if result['type'] == 'numerical':
                            col1, col2 = st.columns(2)

                            with col1:
                                st.write("**Group Means:**")
                                for key, value in result.items():
                                    if 'mean' in key and 'difference' not in key.lower():
                                        st.write(f"- {key}: {value:.4f}")

                            with col2:
                                st.write("**Balance Metrics:**")
                                st.write(f"- SMD: {result.get('standardized_mean_difference', 'N/A'):.4f}")
                                st.write(f"- |SMD|: {result.get('abs_smd', 'N/A'):.4f}")
                                st.write(f"- Balanced: {'Yes' if result['balanced'] else 'No'}")

                            if 'p_value' in result:
                                st.write("**Statistical Test:**")
                                st.write(f"- t-statistic: {result['test_statistic']:.4f}")
                                st.write(f"- p-value: {result['p_value']:.4f}")
                                st.write(f"- Significant: {'Yes' if result['significant'] else 'No'}")

                        else:  # Categorical
                            st.write("**Distributions:**")
                            for group, dist in result.get('distributions', {}).items():
                                st.write(f"\n{group}:")
                                for category, prop in dist.items():
                                    st.write(f"  - {category}: {prop*100:.1f}%")

                            if 'p_value' in result:
                                st.write("\n**Chi-square Test:**")
                                st.write(f"- χ²: {result['chi_square']:.4f}")
                                st.write(f"- p-value: {result['p_value']:.4f}")
                                st.write(f"- Cramér's V: {result['cramers_v']:.4f}")

        elif run_check and len(selected_covariates) == 0:
            st.warning("⚠️ Please select at least one covariate to check balance.")

    else:
        st.info("👈 Please assign treatment groups using the sidebar to begin balance checking.")

else:
    st.error("Failed to load dataset.")
