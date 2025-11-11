"""
Sampling Methods Page - IMPROVED VERSION

Interactive demonstration of sampling techniques with treatment assignment:
- Simple Random Sampling
- Stratified Sampling
- Systematic Sampling
- Cluster Sampling

Improvements:
- Separate treatment/control sample sizes
- Multi-select for balance variables
- Treatment assignment in this tab
- Download includes treatment column
- Link to view assignment health

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

from src.sampling import (
    simple_random_sampling,
    stratified_sampling,
    systematic_sampling,
    cluster_sampling
)
from src.utils.data_loader import load_ecommerce_data

# Page config
st.set_page_config(page_title="Sampling Methods", page_icon="🎲", layout="wide")

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

    /* Fix sidebar navigation text visibility - Issue #9 */
    [data-testid="stSidebar"] .css-1544g2n,
    [data-testid="stSidebar"] a {
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

    /* Fix alignment for section headers - Issue #1 */
    .stMarkdown h2, .stMarkdown h3 {
        margin-top: 2rem;
        margin-bottom: 1rem;
        clear: both;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🎲 Sampling Methods")
st.markdown("Explore different sampling techniques, assign treatment, and check balance.")

# Load data
@st.cache_data
def cached_load_ecommerce_data():
    """Load and cache the e-commerce dataset."""
    try:
        return load_ecommerce_data()
    except Exception as e:
        st.error(f"Failed to load dataset: {str(e)}")
        return None

df = cached_load_ecommerce_data()

if df is not None:
    # Sidebar - Method selection
    st.sidebar.header("⚙️ Sampling Configuration")

    sampling_method = st.sidebar.selectbox(
        "Select Sampling Method",
        ["Simple Random Sampling", "Stratified Sampling", "Systematic Sampling", "Cluster Sampling"]
    )

    st.sidebar.markdown("---")
    st.sidebar.subheader("📊 Sample Size Configuration")

    # IMPROVEMENT 1: Separate treatment and control sample sizes
    treatment_sample_size = st.sidebar.number_input(
        "Treatment Sample Size",
        min_value=10,
        max_value=10000,
        value=500,
        step=10,
        help="Number of observations for treatment group"
    )

    control_sample_size = st.sidebar.number_input(
        "Control Sample Size",
        min_value=10,
        max_value=10000,
        value=500,
        step=10,
        help="Number of observations for control group"
    )

    total_sample_size = treatment_sample_size + control_sample_size

    st.sidebar.info(f"📌 **Total Sample Size:** {total_sample_size:,}")

    # IMPROVEMENT 1: Multi-select for balance variables
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚖️ Variables to Balance")

    all_balance_vars = [
        'age', 'gender', 'location', 'income_level', 'education',
        'total_orders', 'avg_order_value', 'account_age_days',
        'email_open_rate', 'website_visits_per_month',
        'loyalty_program_member', 'mobile_app_user'
    ]

    # Filter to only existing columns
    available_balance_vars = [var for var in all_balance_vars if var in df.columns]

    balance_variables = st.sidebar.multiselect(
        "Select Variables to Balance",
        available_balance_vars,
        default=['age', 'gender', 'income_level', 'total_orders'],
        help="Select independent variables to check balance on after treatment assignment"
    )

    st.sidebar.markdown("---")

    random_seed = st.sidebar.number_input("Random Seed", min_value=0, max_value=9999, value=42)

    # Method-specific parameters
    if sampling_method == "Stratified Sampling":
        # ENHANCEMENT: Multi-select for stratification variables
        stratify_vars = st.sidebar.multiselect(
            "Stratification Variables",
            ["income_level", "location", "gender", "education"],
            default=["income_level"],
            help="Select one or more variables to create cross-strata. Multiple variables ensure better representation across dimensions."
        )

        allocation_method = st.sidebar.radio(
            "Allocation Method",
            ["proportional", "equal"]
        )

        # Show info about multi-variable stratification
        if len(stratify_vars) > 1:
            st.sidebar.info(f"📊 Creating cross-strata from {len(stratify_vars)} variables")
        elif len(stratify_vars) == 0:
            st.sidebar.warning("⚠️ Please select at least one stratification variable")

    elif sampling_method == "Cluster Sampling":
        # Keep single-select for clustering (this is CORRECT!)
        cluster_var = st.sidebar.selectbox(
            "Cluster Variable",
            ["location", "product_category_preference", "education"],
            help="Single natural grouping variable (e.g., geographic location, school, store). Clusters are inherently single-dimensional."
        )
        available_clusters = df[cluster_var].unique() if cluster_var in df.columns else []
        n_clusters_select = st.sidebar.slider(
            "Number of Clusters to Select",
            min_value=1,
            max_value=len(available_clusters) if len(available_clusters) > 0 else 1,
            value=min(2, len(available_clusters)) if len(available_clusters) > 0 else 1
        )

        st.sidebar.info("💡 **Why Single Variable?**\n\nClusters are natural groups (cities, stores, schools). Multi-level clustering (e.g., cities → neighborhoods) is advanced and handled differently.")

    # Run sampling AND assignment button (ONE STEP!)
    run_sampling_and_assignment = st.sidebar.button(
        "🎯 Run Sampling & Assign Treatment",
        type="primary",
        width="stretch",
        help="Samples treatment and control groups separately from the population"
    )

    # Main content
    if sampling_method == "Simple Random Sampling":
        st.header("Simple Random Sampling")

        st.markdown("""
        **Simple Random Sampling** gives each observation an equal probability of selection (P = n/N).
        This is the foundation of probability sampling and eliminates selection bias.

        **When to use:**
        - Population is homogeneous
        - No prior information about subgroups
        - Simplest approach needed
        """)

        if run_sampling_and_assignment:
            with st.spinner("Sampling treatment and control groups..."):
                np.random.seed(random_seed)

                # CORRECT APPROACH: Sample treatment and control separately
                # Step 1: Sample treatment group
                treatment_sample = df.sample(n=treatment_sample_size, random_state=random_seed)
                treatment_sample = treatment_sample.copy()
                treatment_sample['treatment_group'] = 1
                treatment_sample['treatment_label'] = 'Treatment'

                # Step 2: Sample control group from remaining population
                remaining_df = df[~df.index.isin(treatment_sample.index)]
                control_sample = remaining_df.sample(n=control_sample_size, random_state=random_seed+1)
                control_sample = control_sample.copy()
                control_sample['treatment_group'] = 0
                control_sample['treatment_label'] = 'Control'

                # Combine
                final_sample = pd.concat([treatment_sample, control_sample], ignore_index=True)

            st.success(f"✅ Sampling & Assignment Complete!")

            # Store in session state
            st.session_state['sample_with_treatment'] = final_sample
            st.session_state['sampling_method_used'] = sampling_method
            st.session_state['balance_variables'] = balance_variables

            # Issue #2 FIX: Auto-trigger balance checker
            st.session_state['data_with_treatment'] = final_sample
            st.session_state['auto_run_balance_check'] = True
            st.session_state['treatment_col'] = 'treatment_group'
            st.session_state['balance_covariates'] = balance_variables

            # Display summary
            st.subheader("📊 Sample Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Population", f"{len(df):,}")

            with col2:
                st.metric("Treatment", f"{treatment_sample_size:,}",
                         delta=f"{treatment_sample_size/total_sample_size*100:.0f}%")

            with col3:
                st.metric("Control", f"{control_sample_size:,}",
                         delta=f"{control_sample_size/total_sample_size*100:.0f}%")

            with col4:
                st.metric("Total Sample", f"{total_sample_size:,}")

            # Pie chart
            fig = go.Figure(data=[go.Pie(
                labels=['Control', 'Treatment'],
                values=[control_sample_size, treatment_sample_size],
                hole=0.4,
                marker_colors=['#94a3b8', '#38bdf8'],
                textinfo='label+percent+value',
                textfont_size=14
            )])
            fig.update_layout(
                title="Sample Allocation",
                height=300,
                showlegend=True,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1')
            )
            st.plotly_chart(fig, width="stretch")

    elif sampling_method == "Stratified Sampling":
        st.header("Stratified Random Sampling")

        st.markdown("""
        **Stratified Sampling** divides the population into homogeneous subgroups (strata)
        and samples from each stratum. **Both treatment and control groups are stratified separately**
        to ensure balance within each group.

        **Single vs. Multi-Variable Stratification:**
        - **Single Variable** (e.g., income_level): Creates simple strata (Low, Medium, High, Very High)
        - **Multiple Variables** (e.g., income + gender): Creates cross-strata (Low-Male, Low-Female, Medium-Male, etc.)

        **When to use multiple variables:**
        - ✅ When you need representation across multiple important dimensions
        - ✅ For complex populations with multiple defining characteristics
        - ✅ Common in clinical trials (age × gender × disease stage)
        - ⚠️ Warning: Each additional variable multiplies the number of strata
        """)

        if run_sampling_and_assignment:
            # Validate stratification variables selected
            if len(stratify_vars) == 0:
                st.error("❌ Please select at least one stratification variable from the sidebar")
            else:
                with st.spinner("Stratified sampling for treatment and control groups..."):
                    np.random.seed(random_seed)

                    # ENHANCEMENT: Create combined strata column for multi-variable stratification
                    if len(stratify_vars) == 1:
                        # Single variable: use as-is
                        df_with_strata = df.copy()
                        df_with_strata['_strata_'] = df[stratify_vars[0]].astype(str)
                        strata_col = '_strata_'
                    else:
                        # Multiple variables: create combined strata
                        df_with_strata = df.copy()
                        df_with_strata['_strata_'] = df[stratify_vars].apply(
                            lambda row: ' × '.join(row.astype(str)), axis=1
                        )
                        strata_col = '_strata_'

                    # Count strata
                    n_strata = df_with_strata[strata_col].nunique()

                    if n_strata > 50:
                        st.warning(f"⚠️ {n_strata} strata detected! This may result in very small sample sizes per stratum. Consider using fewer stratification variables.")

                    # CORRECT APPROACH: Stratify treatment and control separately

                    # Helper function for stratified sampling
                    def stratify_sample(data, strata_col, n, seed, allocation='proportional'):
                        """Sample n observations with stratification."""
                        strata_counts = data[strata_col].value_counts()
                        samples = []

                        for stratum in strata_counts.index:
                            stratum_data = data[data[strata_col] == stratum]

                            if allocation == 'proportional':
                                # Proportional to stratum size
                                n_stratum = int(np.round(n * (len(stratum_data) / len(data))))
                                n_stratum = max(1, min(n_stratum, len(stratum_data)))
                            else:  # equal
                                n_stratum = n // len(strata_counts)
                                n_stratum = min(n_stratum, len(stratum_data))

                            if n_stratum > 0 and len(stratum_data) > 0:
                                stratum_sample = stratum_data.sample(n=min(n_stratum, len(stratum_data)), random_state=seed)
                                samples.append(stratum_sample)

                        return pd.concat(samples, ignore_index=True) if samples else pd.DataFrame()

                    # Step 1: Stratified sample for TREATMENT group
                    treatment_sample = stratify_sample(
                        df_with_strata, strata_col, treatment_sample_size, random_seed, allocation_method
                    )
                    treatment_sample['treatment_group'] = 1
                    treatment_sample['treatment_label'] = 'Treatment'

                    # Step 2: Stratified sample for CONTROL group (from remaining)
                    remaining_df = df_with_strata[~df_with_strata.index.isin(treatment_sample.index)]
                    control_sample = stratify_sample(
                        remaining_df, strata_col, control_sample_size, random_seed+1, allocation_method
                    )
                    control_sample['treatment_group'] = 0
                    control_sample['treatment_label'] = 'Control'

                    # Combine (drop the temporary strata column)
                    final_sample = pd.concat([treatment_sample, control_sample], ignore_index=True)
                    if '_strata_' in final_sample.columns:
                        final_sample = final_sample.drop(columns=['_strata_'])

                st.success(f"✅ Stratified Sampling & Assignment Complete!")

                # Display stratification info
                if len(stratify_vars) == 1:
                    st.info(f"📌 Stratified by: **{stratify_vars[0]}**")
                else:
                    st.info(f"📌 Cross-stratified by: **{' × '.join(stratify_vars)}** ({n_strata} combined strata)")

            # Store in session state
            st.session_state['sample_with_treatment'] = final_sample
            st.session_state['sampling_method_used'] = sampling_method
            st.session_state['balance_variables'] = balance_variables

            # Issue #2 FIX: Auto-trigger balance checker
            st.session_state['data_with_treatment'] = final_sample
            st.session_state['auto_run_balance_check'] = True
            st.session_state['treatment_col'] = 'treatment_group'
            st.session_state['balance_covariates'] = balance_variables

            # Display summary
            st.subheader("📊 Sample Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Population", f"{len(df):,}")

            with col2:
                st.metric("Treatment", f"{treatment_sample_size:,}",
                         delta=f"{treatment_sample_size/total_sample_size*100:.0f}%")

            with col3:
                st.metric("Control", f"{control_sample_size:,}",
                         delta=f"{control_sample_size/total_sample_size*100:.0f}%")

            with col4:
                st.metric("Total Sample", f"{total_sample_size:,}")

                # Stratification balance comparison
                strata_label = ' × '.join(stratify_vars) if len(stratify_vars) > 1 else stratify_vars[0]
                st.subheader(f"📊 Stratification Balance ({strata_label})")

                # Recreate combined strata for display
                if len(stratify_vars) == 1:
                    treatment_sample['_display_strata_'] = treatment_sample[stratify_vars[0]].astype(str)
                    control_sample['_display_strata_'] = control_sample[stratify_vars[0]].astype(str)
                    df_display = df.copy()
                    df_display['_display_strata_'] = df[stratify_vars[0]].astype(str)
                else:
                    treatment_sample['_display_strata_'] = treatment_sample[stratify_vars].apply(
                        lambda row: ' × '.join(row.astype(str)), axis=1
                    )
                    control_sample['_display_strata_'] = control_sample[stratify_vars].apply(
                        lambda row: ' × '.join(row.astype(str)), axis=1
                    )
                    df_display = df.copy()
                    df_display['_display_strata_'] = df[stratify_vars].apply(
                        lambda row: ' × '.join(row.astype(str)), axis=1
                    )

                # Visualizations
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**Treatment Group Distribution**")
                    treatment_dist = treatment_sample['_display_strata_'].value_counts().sort_index()

                    # Use bar chart if too many strata
                    if len(treatment_dist) > 8:
                        fig1 = px.bar(
                            x=treatment_dist.index,
                            y=treatment_dist.values,
                            title=f"Treatment (n={len(treatment_sample)})",
                            labels={'x': 'Stratum', 'y': 'Count'},
                            color_discrete_sequence=['#3b82f6']
                        )
                        fig1.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#cbd5e1'),
                            xaxis_tickangle=-45
                        )
                    else:
                        fig1 = px.pie(
                            values=treatment_dist.values,
                            names=treatment_dist.index,
                            title=f"Treatment (n={len(treatment_sample)})",
                            color_discrete_sequence=px.colors.sequential.Blues
                        )
                        fig1.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#cbd5e1'))

                    st.plotly_chart(fig1, width="stretch")

                with col2:
                    st.markdown("**Control Group Distribution**")
                    control_dist = control_sample['_display_strata_'].value_counts().sort_index()

                    # Use bar chart if too many strata
                    if len(control_dist) > 8:
                        fig2 = px.bar(
                            x=control_dist.index,
                            y=control_dist.values,
                            title=f"Control (n={len(control_sample)})",
                            labels={'x': 'Stratum', 'y': 'Count'},
                            color_discrete_sequence=['#6b7280']
                        )
                        fig2.update_layout(
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color='#cbd5e1'),
                            xaxis_tickangle=-45
                        )
                    else:
                        fig2 = px.pie(
                            values=control_dist.values,
                            names=control_dist.index,
                            title=f"Control (n={len(control_sample)})",
                            color_discrete_sequence=px.colors.sequential.Greys
                        )
                        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#cbd5e1'))

                    st.plotly_chart(fig2, width="stretch")

                # Stratum-level table
                st.markdown("**Stratum-Level Breakdown**")

                stratum_breakdown = []
                all_strata = df_display['_display_strata_'].unique()

                for stratum in sorted(all_strata):
                    t_count = (treatment_sample['_display_strata_'] == stratum).sum()
                    c_count = (control_sample['_display_strata_'] == stratum).sum()
                    total_count = t_count + c_count
                    pop_count = (df_display['_display_strata_'] == stratum).sum()

                    if total_count > 0:  # Only show strata that have samples
                        stratum_breakdown.append({
                            'Stratum': stratum,
                            'Population': pop_count,
                            'Treatment': t_count,
                            'Control': c_count,
                            'Total Sampled': total_count,
                            'Treatment %': f"{t_count/len(treatment_sample)*100:.1f}%" if len(treatment_sample) > 0 else "0%",
                            'Control %': f"{c_count/len(control_sample)*100:.1f}%" if len(control_sample) > 0 else "0%"
                        })

                breakdown_df = pd.DataFrame(stratum_breakdown)

                # Add summary row
                summary_row = pd.DataFrame([{
                    'Stratum': '**TOTAL**',
                    'Population': len(df_display),
                    'Treatment': len(treatment_sample),
                    'Control': len(control_sample),
                    'Total Sampled': len(treatment_sample) + len(control_sample),
                    'Treatment %': '100%',
                    'Control %': '100%'
                }])
                breakdown_df = pd.concat([breakdown_df, summary_row], ignore_index=True)

                st.dataframe(breakdown_df, width="stretch")

                # Efficiency metrics
                if len(stratify_vars) > 1:
                    st.markdown("---")
                    st.markdown("**🎯 Multi-Variable Stratification Benefits:**")
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.metric("Variables Combined", len(stratify_vars))

                    with col2:
                        st.metric("Cross-Strata Created", n_strata)

                    with col3:
                        avg_stratum_size = len(df_display) / n_strata
                        st.metric("Avg. Stratum Size", f"{avg_stratum_size:.0f}")

                    st.success("✅ Sampling is balanced across all " + " × ".join(stratify_vars) + " combinations!")

                # Clean up temporary column
                if '_display_strata_' in treatment_sample.columns:
                    treatment_sample = treatment_sample.drop(columns=['_display_strata_'])
                if '_display_strata_' in control_sample.columns:
                    control_sample = control_sample.drop(columns=['_display_strata_'])

    elif sampling_method == "Systematic Sampling":
        st.header("Systematic Sampling")

        st.markdown("""
        **Systematic Sampling** selects every kth element after a random start.
        **Treatment and control are sampled with different intervals** for proper allocation.
        """)

        if run_sampling_and_assignment:
            with st.spinner("Systematic sampling for treatment and control..."):
                np.random.seed(random_seed)

                # Calculate intervals for each group
                k_treatment = len(df) / treatment_sample_size
                k_control = len(df) / control_sample_size

                # Sample treatment (every k_treatment)
                start_t = np.random.randint(0, int(k_treatment))
                treatment_indices = list(range(start_t, len(df), int(k_treatment)))[:treatment_sample_size]
                treatment_sample = df.iloc[treatment_indices].copy()
                treatment_sample['treatment_group'] = 1
                treatment_sample['treatment_label'] = 'Treatment'

                # Sample control (every k_control from remaining)
                remaining_indices = [i for i in range(len(df)) if i not in treatment_indices]
                start_c = np.random.randint(0, min(int(k_control), len(remaining_indices)))
                control_indices = [remaining_indices[i] for i in range(start_c, len(remaining_indices), int(k_control))][:control_sample_size]
                control_sample = df.iloc[control_indices].copy()
                control_sample['treatment_group'] = 0
                control_sample['treatment_label'] = 'Control'

                # Combine
                final_sample = pd.concat([treatment_sample, control_sample], ignore_index=True)

            st.success(f"✅ Systematic Sampling & Assignment Complete!")

            # Store in session state
            st.session_state['sample_with_treatment'] = final_sample
            st.session_state['sampling_method_used'] = sampling_method
            st.session_state['balance_variables'] = balance_variables

            # Issue #2 FIX: Auto-trigger balance checker
            st.session_state['data_with_treatment'] = final_sample
            st.session_state['auto_run_balance_check'] = True
            st.session_state['treatment_col'] = 'treatment_group'
            st.session_state['balance_covariates'] = balance_variables

            # Display summary
            st.subheader("📊 Sample Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Treatment Interval", f"k={k_treatment:.1f}")

            with col2:
                st.metric("Control Interval", f"k={k_control:.1f}")

            with col3:
                st.metric("Treatment", f"{treatment_sample_size:,}")

            with col4:
                st.metric("Control", f"{control_sample_size:,}")

    else:  # Cluster Sampling
        st.header("Cluster Sampling")

        st.markdown("""
        **Cluster Sampling** divides the population into clusters, randomly selects clusters,
        and assigns treatment/control within selected clusters.
        """)

        if run_sampling_and_assignment:
            with st.spinner("Cluster sampling for treatment and control..."):
                np.random.seed(random_seed)

                # Select clusters
                available_clusters = df[cluster_var].unique()
                selected_clusters = np.random.choice(
                    available_clusters,
                    size=min(n_clusters_select, len(available_clusters)),
                    replace=False
                )

                # Get all observations from selected clusters
                cluster_sample = df[df[cluster_var].isin(selected_clusters)].copy()

                # Now assign treatment/control within the cluster sample
                # Sample treatment from cluster_sample
                treatment_sample = cluster_sample.sample(n=min(treatment_sample_size, len(cluster_sample)),
                                                         random_state=random_seed)
                treatment_sample['treatment_group'] = 1
                treatment_sample['treatment_label'] = 'Treatment'

                # Sample control from remaining in cluster_sample
                remaining_cluster = cluster_sample[~cluster_sample.index.isin(treatment_sample.index)]
                control_sample = remaining_cluster.sample(n=min(control_sample_size, len(remaining_cluster)),
                                                          random_state=random_seed+1)
                control_sample['treatment_group'] = 0
                control_sample['treatment_label'] = 'Control'

                # Combine
                final_sample = pd.concat([treatment_sample, control_sample], ignore_index=True)

            st.success(f"✅ Cluster Sampling & Assignment Complete!")

            st.info(f"📌 Selected {len(selected_clusters)} clusters: {list(selected_clusters)}")

            # Store in session state
            st.session_state['sample_with_treatment'] = final_sample
            st.session_state['sampling_method_used'] = sampling_method
            st.session_state['balance_variables'] = balance_variables

            # Issue #2 FIX: Auto-trigger balance checker
            st.session_state['data_with_treatment'] = final_sample
            st.session_state['auto_run_balance_check'] = True
            st.session_state['treatment_col'] = 'treatment_group'
            st.session_state['balance_covariates'] = balance_variables

            # Display summary
            st.subheader("📊 Sample Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Clusters Selected", f"{len(selected_clusters)}")

            with col2:
                st.metric("Treatment", f"{len(treatment_sample):,}")

            with col3:
                st.metric("Control", f"{len(control_sample):,}")

            with col4:
                st.metric("Total Sample", f"{len(final_sample):,}")

    # Download & Navigation section (appears after sampling+assignment)
    if 'sample_with_treatment' in st.session_state:
        st.markdown("---")

        # Issue #2 FIX: Prominent call-to-action for Balance Checker
        st.success("✅ **Sampling & Treatment Assignment Complete!**")
        st.info("👉 **Next Step:** View balance checker results automatically populated below, or navigate to Balance Checker page for detailed analysis.")

        # Auto-generated balance info box
        st.markdown("""
        <div style="background-color: #1e3a2e; padding: 1.5rem; border-radius: 10px; border-left: 5px solid #4ade80; margin: 1rem 0;">
            <h3 style="color: #4ade80; margin-top: 0;">🎯 Balance Checking Ready!</h3>
            <p style="color: #cbd5e1; margin-bottom: 0.5rem;">Your sample is ready for balance validation. Navigate to <strong>Balance Checker</strong> page to:</p>
            <ul style="color: #cbd5e1;">
                <li>View standardized mean differences (SMD)</li>
                <li>See interactive Love Plot</li>
                <li>Check statistical test results</li>
                <li>Get overall balance score</li>
            </ul>
            <p style="color: #4ade80; font-weight: bold; margin-top: 1rem;">👈 Click "Balance Checker" in the sidebar to view results!</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.header("💾 Download Sample")

        col1, col2 = st.columns(2)

        with col1:
            # Download button
            sample_to_download = st.session_state['sample_with_treatment']

            csv = sample_to_download.to_csv(index=False)
            st.download_button(
                label="📥 Download Sample with Treatment Assignment",
                data=csv,
                file_name=f"sample_{sampling_method.lower().replace(' ', '_')}_with_treatment.csv",
                mime="text/csv",
                width="stretch"
            )

            st.info("✅ CSV includes 'treatment_group' and 'treatment_label' columns")

        with col2:
            st.markdown("### 📊 Sample Info")
            st.write(f"**Method:** {sampling_method}")
            st.write(f"**Total Sample:** {len(sample_to_download):,}")
            st.write(f"**Treatment:** {(sample_to_download['treatment_group']==1).sum():,}")
            st.write(f"**Control:** {(sample_to_download['treatment_group']==0).sum():,}")
            if balance_variables:
                st.write(f"**Balance Variables:** {len(balance_variables)} selected")

        # Preview of sample with treatment
        st.markdown("---")
        st.subheader("👀 Sample Preview (with Treatment Assignment)")

        # Show treatment distribution
        preview_df = st.session_state['sample_with_treatment']

        col1, col2 = st.columns([3, 1])

        with col1:
            # Show first 10 rows
            display_cols = ['customer_id', 'age', 'gender', 'income_level', 'total_orders',
                           'treatment_group', 'treatment_label']
            display_cols = [col for col in display_cols if col in preview_df.columns]

            st.dataframe(preview_df[display_cols].head(10), width="stretch")

        with col2:
            st.markdown("**Treatment Summary:**")
            st.write(f"Treatment: {(preview_df['treatment_group']==1).sum():,}")
            st.write(f"Control: {(preview_df['treatment_group']==0).sum():,}")

            if balance_variables:
                st.markdown("**Balance Variables:**")
                for var in balance_variables[:5]:
                    st.write(f"- {var}")
                if len(balance_variables) > 5:
                    st.write(f"- ... +{len(balance_variables)-5} more")

    elif 'current_sample' in st.session_state and st.session_state['current_sample'] is not None:
        # Sample created but no treatment assigned yet
        st.markdown("---")
        st.info("👆 **Next Step:** Configure treatment assignment above and click '🎯 Assign Treatment & Control'")

else:
    st.error("Failed to load dataset.")
