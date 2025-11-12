"""
Experimental Designs Page

Interactive demonstration of classical experimental design methods:
- Completely Randomized Design (CRD)
- Randomized Block Design (RBD)
- Factorial Design (2^k and multi-factor)

Each design can be created, visualized, and analyzed with simulated or real response data.

Author: DOE Simulator Team
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.experimental_designs.completely_randomized import CompletelyRandomizedDesign
from src.experimental_designs.randomized_block import RandomizedBlockDesign
from src.experimental_designs.factorial_design import FactorialDesign
from src.experimental_designs.fractional_factorial import FractionalFactorialDesign, COMMON_DESIGNS
from src.experimental_designs.response_surface import CentralCompositeDesign, BoxBehnkenDesign
from src.utils.data_loader import load_ecommerce_data

# Page config
st.set_page_config(page_title="Experimental Designs", page_icon="**", layout="wide")

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

    .info-box {
        background-color: #334155;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #38bdf8;
        margin: 1rem 0;
        color: #cbd5e1;
    }

    .success-box {
        background-color: #1e3a2e;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #4ade80;
        margin: 1rem 0;
        color: #cbd5e1;
    }

    .warning-box {
        background-color: #3a3020;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #facc15;
        margin: 1rem 0;
        color: #cbd5e1;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.title("🔬 Experimental Designs")
st.markdown("""
Design and analyze controlled experiments using classical DOE methods.
Choose a design type, configure parameters, and see the results!
""")

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
    # Sidebar - Design selection
    st.sidebar.header("⚙️ Design Configuration")

    # Issue #8 FIX: Add Fractional Factorial option
    design_type = st.sidebar.selectbox(
        "Select Design Type",
        ["Completely Randomized Design (CRD)",
         "Randomized Block Design (RBD)",
         "Factorial Design (2^k)",
         "Fractional Factorial Design (2^(k-p))",  # NEW!
         "Response Surface Method (CCD)",
         "Box-Behnken Design"],
        help="Select the experimental design type based on your research needs"
    )

    st.sidebar.markdown("---")

    # Design-specific configuration
    if design_type == "Completely Randomized Design (CRD)":
        st.header("Completely Randomized Design (CRD)")

        st.markdown("""
        <div class="info-box">
        <strong>What is CRD?</strong><br>
        The simplest experimental design where treatments are randomly assigned to experimental units.
        Best used when units are homogeneous with no known sources of systematic variation.
        <br><br>
        <strong>Model:</strong> Y<sub>ij</sub> = μ + τ<sub>i</sub> + ε<sub>ij</sub>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.subheader("CRD Parameters")

        # Treatment configuration
        n_treatments = st.sidebar.number_input(
            "Number of Treatments",
            min_value=2,
            max_value=10,
            value=4,
            help=" Number of different treatments to compare (including control). Example: Control + 3 treatments = 4 total"
        )

        treatment_names = []
        for i in range(n_treatments):
            default_name = f"Treatment_{chr(65+i)}" if i > 0 else "Control"
            treatment_name = st.sidebar.text_input(
                f"Treatment {i+1} Name",
                value=default_name,
                key=f"crd_treatment_{i}"
            )
            treatment_names.append(treatment_name)

        sample_size = st.sidebar.number_input(
            "Total Sample Size",
            min_value=n_treatments * 2,
            max_value=min(5000, len(df)),
            value=min(1000, len(df)),
            step=10
        )

        allocation = st.sidebar.radio(
            "Sample Allocation",
            ["Equal", "Custom"],
            help=" Equal: Same sample size for each treatment. Custom: Specify different sizes per treatment (useful for unequal designs)"
        )

        sample_sizes = {}
        if allocation == "Custom":
            st.sidebar.markdown("**Custom Allocation:**")
            remaining = sample_size
            for i, treatment in enumerate(treatment_names[:-1]):
                size = st.sidebar.number_input(
                    f"{treatment} size",
                    min_value=1,
                    max_value=remaining,
                    value=sample_size // n_treatments,
                    key=f"crd_size_{i}"
                )
                sample_sizes[treatment] = size
                remaining -= size
            # Last treatment gets remainder
            sample_sizes[treatment_names[-1]] = remaining
        else:
            # Equal allocation
            base_size = sample_size // n_treatments
            remainder = sample_size % n_treatments
            sample_sizes = {
                t: base_size + (1 if i < remainder else 0)
                for i, t in enumerate(treatment_names)
            }

        random_seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=9999)

        # Create design button
        if st.sidebar.button(" Create CRD", type="primary"):
            with st.spinner("Creating Completely Randomized Design..."):
                # Create design
                crd = CompletelyRandomizedDesign(random_seed=random_seed)

                # Sample from dataset
                sample_data = df.sample(n=sample_size, random_state=random_seed)

                design = crd.create_design(
                    data=sample_data,
                    treatments=treatment_names,
                    sample_sizes=sample_sizes,
                    balance_check=True
                )

                st.session_state['current_design'] = design
                st.session_state['design_object'] = crd
                st.session_state['design_type'] = 'CRD'

            st.success("✅ CRD created successfully!")

        # Display design if created
        if 'current_design' in st.session_state and st.session_state.get('design_type') == 'CRD':
            design = st.session_state['current_design']
            crd = st.session_state['design_object']

            st.markdown("---")
            st.subheader(" Design Summary")

            # Metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Units", len(design))

            with col2:
                st.metric("Treatments", n_treatments)

            with col3:
                st.metric("Min Group Size", min(sample_sizes.values()))

            with col4:
                st.metric("Max Group Size", max(sample_sizes.values()))

            # Treatment allocation pie chart
            st.subheader("Treatment Allocation")

            treatment_counts = design['treatment'].value_counts()

            fig = px.pie(
                values=treatment_counts.values,
                names=treatment_counts.index,
                title="Sample Distribution by Treatment",
                color_discrete_sequence=px.colors.sequential.Blues
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1'),
                height=400
            )
            st.plotly_chart(fig, width="stretch")

            # Show design table
            st.subheader("Design Table (First 20 Rows)")
            display_cols = ['customer_id', 'treatment', 'age', 'gender', 'income_level', 'total_orders']
            display_cols = [col for col in display_cols if col in design.columns]
            st.dataframe(design[display_cols].head(20), width="stretch")

            # Simulate response and analyze
            st.markdown("---")
            st.subheader(" Simulate Response & Analyze")

            col1, col2 = st.columns(2)

            with col1:
                response_var = st.selectbox(
                    "Response Variable (for simulation)",
                    ['conversion_rate', 'lifetime_value', 'avg_order_value']
                )

            with col2:
                treatment_effect = st.slider(
                    "Treatment Effect Size",
                    min_value=0.0,
                    max_value=20.0,
                    value=5.0,
                    step=0.5,
                    help="How much effect does the best treatment have?"
                )

            if st.button(" Simulate & Analyze"):
                # Simulate response with treatment effects
                design['response'] = design[response_var].copy() if response_var in design.columns else np.random.randn(len(design)) * 10 + 50

                # Add differential treatment effects
                for i, treatment in enumerate(treatment_names):
                    effect = treatment_effect * (i / max(1, n_treatments - 1))  # Linear increase
                    design.loc[design['treatment'] == treatment, 'response'] += effect

                # Add noise
                design['response'] += np.random.randn(len(design)) * 3

                # Analyze
                results = crd.analyze_design(design, response_var='response')

                st.session_state['crd_results'] = results
                st.session_state['crd_design_with_response'] = design

                # Display results
                st.markdown("---")
                st.subheader(" ANOVA Results")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric(
                        "F-Statistic",
                        f"{results['anova']['f_statistic']:.4f}",
                        delta="Significant" if results['anova']['significant'] else "Not Significant"
                    )

                with col2:
                    st.metric("P-Value", f"{results['anova']['p_value']:.4f}")

                with col3:
                    st.metric(
                        "Effect Size (η²)",
                        f"{results['effect_size']['eta_squared']:.4f}",
                        delta=results['effect_size']['interpretation']
                    )

                # Treatment means
                st.subheader("Treatment Means")

                means_df = pd.DataFrame(results['treatment_statistics']).T
                means_df = means_df.round(4)

                st.dataframe(means_df, width="stretch")

                # Visualization
                fig = go.Figure()

                for treatment, stats in results['treatment_statistics'].items():
                    fig.add_trace(go.Bar(
                        name=treatment,
                        x=[treatment],
                        y=[stats['mean']],
                        error_y=dict(type='data', array=[stats['se']], visible=True),
                        text=f"{stats['mean']:.2f}",
                        textposition='outside'
                    ))

                fig.update_layout(
                    title="Treatment Means with Standard Error",
                    yaxis_title="Mean Response",
                    xaxis_title="Treatment",
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=dict(color='#cbd5e1'),
                    height=400
                )

                st.plotly_chart(fig, width="stretch")

    elif design_type == "Randomized Block Design (RBD)":
        st.header("Randomized Block Design (RBD)")

        st.markdown("""
        <div class="info-box">
        <strong>What is RBD?</strong><br>
        Accounts for one source of systematic variation by grouping units into blocks,
        then randomizing treatments within each block. Increases precision by removing
        block-to-block variation from experimental error.
        <br><br>
        <strong>Model:</strong> Y<sub>ij</sub> = μ + τ<sub>i</sub> + β<sub>j</sub> + ε<sub>ij</sub>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.subheader("RBD Parameters")

        # Issue #4 FIX: Multi-select for blocking variables
        potential_blocks = ['location', 'income_level', 'education', 'product_category_preference']
        potential_blocks = [col for col in potential_blocks if col in df.columns]

        block_vars = st.sidebar.multiselect(
            "Blocking Variables",
            potential_blocks,
            default=[potential_blocks[0]] if potential_blocks else [],
            help="Select one or more nuisance factors to block. Multiple variables create combined blocks (e.g., Location × Time_of_Day)"
        )

        if len(block_vars) == 0:
            st.sidebar.warning(" Please select at least one blocking variable")
        elif len(block_vars) > 1:
            st.sidebar.info(f" Creating combined blocks from {len(block_vars)} variables")

        # Treatment configuration
        n_treatments = st.sidebar.number_input(
            "Number of Treatments",
            min_value=2,
            max_value=10,
            value=4
        )

        treatment_names = []
        for i in range(n_treatments):
            default_name = f"Treatment_{chr(65+i)}" if i > 0 else "Control"
            treatment_name = st.sidebar.text_input(
                f"Treatment {i+1} Name",
                value=default_name,
                key=f"rbd_treatment_{i}"
            )
            treatment_names.append(treatment_name)

        # Issue #6 FIX: Add custom allocation option for RBD
        allocation_rbd = st.sidebar.radio(
            "Treatment Allocation",
            ["Equal (Balanced RBD)", "Custom (Unequal Sizes)"],
            help=" Equal: Each treatment gets same number of units per block. Custom: Specify different allocation"
        )

        replications = st.sidebar.number_input(
            "Replications per Block",
            min_value=1,
            max_value=5,
            value=1,
            help=" Number of times each treatment is replicated within each block. More replications = more power to detect effects"
        )

        random_seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=9999, key="rbd_seed")

        # Create design button
        if st.sidebar.button(" Create RBD", type="primary"):
            if len(block_vars) == 0:
                st.error("❌ Please select at least one blocking variable from the sidebar")
            else:
                with st.spinner("Creating Randomized Block Design..."):
                    rbd = RandomizedBlockDesign(random_seed=random_seed)

                    # Issue #4 FIX: Create combined block column for multi-variable blocking
                    df_with_blocks = df.copy()
                    if len(block_vars) == 1:
                        df_with_blocks['_block_'] = df[block_vars[0]].astype(str)
                    else:
                        df_with_blocks['_block_'] = df[block_vars].apply(
                            lambda row: ' × '.join(row.astype(str)), axis=1
                        )

                    design = rbd.create_design(
                        data=df_with_blocks,
                        treatments=treatment_names,
                        block_col='_block_',
                        replications=replications,
                        check_completeness=False
                    )

                    st.session_state['current_design'] = design
                    st.session_state['design_object'] = rbd
                    st.session_state['design_type'] = 'RBD'
                    st.session_state['block_col'] = '_block_'
                    st.session_state['block_vars'] = block_vars
                    st.session_state['n_blocks'] = design['_block_'].nunique()

                if len(block_vars) == 1:
                    st.success(f"✅ RBD created with blocking by **{block_vars[0]}**!")
                else:
                    st.success(f"✅ RBD created with combined blocking by **{' × '.join(block_vars)}**!")
                    st.info(f" Created {design['_block_'].nunique()} combined blocks")

        # Display design
        if 'current_design' in st.session_state and st.session_state.get('design_type') == 'RBD':
            design = st.session_state['current_design']
            rbd = st.session_state['design_object']
            block_col = st.session_state['block_col']

            design = design[design['treatment'].notna()]

            st.markdown("---")
            st.subheader(" Design Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Total Units Assigned", len(design))

            with col2:
                st.metric("Treatments", n_treatments)

            with col3:
                st.metric("Blocks", design[block_col].nunique())

            with col4:
                st.metric("Replications", replications)

            # Treatment × Block crosstab
            st.subheader("Treatment × Block Design")

            crosstab = pd.crosstab(design[block_col], design['treatment'])
            st.dataframe(crosstab, width="stretch")

            # Heatmap
            fig = px.imshow(
                crosstab.values,
                labels=dict(x="Treatment", y="Block", color="Count"),
                x=crosstab.columns,
                y=crosstab.index,
                color_continuous_scale='Blues',
                title="Design Matrix Heatmap"
            )
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color='#cbd5e1'),
                height=400
            )
            st.plotly_chart(fig, width="stretch")

            # Simulate and analyze
            st.markdown("---")
            st.subheader("🧪 Simulate Response & Analyze")

            response_var = st.selectbox(
                "Response Variable (for simulation)",
                ['conversion_rate', 'lifetime_value', 'avg_order_value'],
                key="rbd_response"
            )

            treatment_effect = st.slider(
                "Treatment Effect Size",
                min_value=0.0,
                max_value=20.0,
                value=5.0,
                step=0.5,
                key="rbd_effect"
            )

            if st.button(" Simulate & Analyze", key="rbd_analyze"):
                # Simulate response
                design['response'] = design[response_var].copy() if response_var in design.columns else np.random.randn(len(design)) * 10 + 50

                # Add block effects (systematic differences)
                blocks = design[block_col].unique()
                block_effects = {block: np.random.randn() * 5 for block in blocks}
                for block, effect in block_effects.items():
                    design.loc[design[block_col] == block, 'response'] += effect

                # Add treatment effects
                for i, treatment in enumerate(treatment_names):
                    effect = treatment_effect * (i / max(1, n_treatments - 1))
                    design.loc[design['treatment'] == treatment, 'response'] += effect

                # Add noise
                design['response'] += np.random.randn(len(design)) * 2

                # Analyze
                results = rbd.analyze_design(design, response_var='response', block_col=block_col)

                # Display results
                st.markdown("---")
                st.subheader(" Two-Way ANOVA Results")

                # Treatment effect
                st.markdown("**Treatment Effect:**")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("F-Statistic", f"{results['anova_table']['treatment']['f_statistic']:.4f}")

                with col2:
                    st.metric("P-Value", f"{results['anova_table']['treatment']['p_value']:.4f}")

                with col3:
                    st.metric("η²", f"{results['effect_sizes']['treatment_eta_squared']:.4f}")

                # Block effect
                st.markdown("**Block Effect:**")
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("F-Statistic", f"{results['anova_table']['block']['f_statistic']:.4f}")

                with col2:
                    st.metric("P-Value", f"{results['anova_table']['block']['p_value']:.4f}")

                with col3:
                    st.metric("η²", f"{results['effect_sizes']['block_eta_squared']:.4f}")

                # Relative efficiency
                st.markdown("**Efficiency Comparison:**")
                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Relative Efficiency vs CRD",
                        f"{results['relative_efficiency']['vs_crd']:.2f}",
                        delta=f"{results['relative_efficiency']['percent_improvement']:.1f}%"
                    )

                with col2:
                    st.info(results['relative_efficiency']['interpretation'])

    elif design_type == "Factorial Design (2^k)":
        st.header("Factorial Design (2^k)")

        st.markdown("""
        <div class="info-box">
        <strong>What is Factorial Design?</strong><br>
        Tests multiple factors simultaneously, including their interactions.
        More efficient than one-factor-at-a-time experiments and reveals synergistic/antagonistic effects.
        <br><br>
        <strong>Model:</strong> Y = μ + Σα<sub>i</sub> + ΣΣ(αβ)<sub>ij</sub> + ... + ε
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.subheader("Factorial Design Parameters")

        n_factors = st.sidebar.number_input(
            "Number of Factors",
            min_value=2,
            max_value=4,
            value=3,
            help=" Number of independent variables to test. Factorial design tests all combinations of factor levels"
        )

        factors = {}
        for i in range(n_factors):
            st.sidebar.markdown(f"**Factor {i+1}:**")

            factor_name = st.sidebar.text_input(
                f"Factor {i+1} Name",
                value=f"Factor_{chr(65+i)}",
                key=f"factorial_name_{i}"
            )

            n_levels = st.sidebar.selectbox(
                f"{factor_name} Levels",
                [2, 3],
                key=f"factorial_levels_{i}"
            )

            levels = []
            for j in range(n_levels):
                level = st.sidebar.text_input(
                    f"  Level {j+1}",
                    value=f"Level_{j+1}",
                    key=f"factorial_level_{i}_{j}"
                )
                levels.append(level)

            factors[factor_name] = levels

        replications = st.sidebar.number_input(
            "Replications",
            min_value=1,
            max_value=10,
            value=2,
            help=" Number of times each treatment combination is repeated. Replications improve precision and allow estimation of pure error"
        )

        random_seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=9999, key="factorial_seed")

        # Create design
        if st.sidebar.button(" Create Factorial Design", type="primary"):
            with st.spinner("Creating Factorial Design..."):
                factorial = FactorialDesign(random_seed=random_seed)

                design = factorial.create_design(
                    factors=factors,
                    replications=replications,
                    randomize=True
                )

                st.session_state['current_design'] = design
                st.session_state['design_object'] = factorial
                st.session_state['design_type'] = 'Factorial'
                st.session_state['factors'] = factors

            st.success("✅ Factorial Design created successfully!")

        # Display design
        if 'current_design' in st.session_state and st.session_state.get('design_type') == 'Factorial':
            design = st.session_state['current_design']
            factorial = st.session_state['design_object']
            factors = st.session_state['factors']

            st.markdown("---")
            st.subheader(" Design Summary")

            summary = factorial.get_design_summary()

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Factors", summary['n_factors'])

            with col2:
                st.metric("Treatment Combinations", summary['n_combinations'])

            with col3:
                st.metric("Replications", summary['replications'])

            with col4:
                st.metric("Total Runs", summary['total_runs'])

            # Show design matrix
            st.subheader("Design Matrix")

            factor_cols = list(factors.keys())
            display_cols = factor_cols + ['replication', 'std_order', 'run_order']
            st.dataframe(design[display_cols], width="stretch")

            # Simulate response
            st.markdown("---")
            st.subheader(" Simulate Response & Analyze")

            if st.button(" Simulate & Analyze Effects", key="factorial_analyze"):
                # Simulate response with main effects and interactions
                design['response'] = 100  # Baseline

                # Add main effects (linear increase across factor levels)
                for i, (factor, levels) in enumerate(factors.items()):
                    for j, level in enumerate(levels):
                        effect = 5 * (i + 1) * (j / len(levels))
                        design.loc[design[factor] == level, 'response'] += effect

                # Add interaction (only for first two factors)
                if len(factors) >= 2:
                    factor_names = list(factors.keys())
                    factor_1 = factor_names[0]
                    factor_2 = factor_names[1]

                    # Synergistic interaction
                    design.loc[
                        (design[factor_1] == factors[factor_1][-1]) &
                        (design[factor_2] == factors[factor_2][-1]),
                        'response'
                    ] += 10  # Extra boost!

                # Add noise
                design['response'] += np.random.randn(len(design)) * 3

                # Analyze
                results = factorial.analyze_effects(
                    design,
                    response_var='response',
                    include_interactions=True,
                    max_interaction_order=2
                )

                st.markdown("---")
                st.subheader(" Main Effects")

                for factor, effect in results['main_effects'].items():
                    with st.expander(f"**{factor}** (F={effect['f_statistic']:.2f}, p={effect['p_value']:.4f})"):
                        col1, col2 = st.columns(2)

                        with col1:
                            st.write("**Statistics:**")
                            st.write(f"- F-statistic: {effect['f_statistic']:.4f}")
                            st.write(f"- P-value: {effect['p_value']:.4f}")
                            st.write(f"- Effect size (η²): {effect['eta_squared']:.4f}")
                            st.write(f"- Interpretation: {effect['interpretation']}")

                        with col2:
                            st.write("**Level Means:**")
                            for level, mean in effect['means'].items():
                                st.write(f"- {level}: {mean:.2f}")

                st.subheader(" Interaction Effects")

                if results['interactions']:
                    for interaction, effect in results['interactions'].items():
                        sig_marker = "✅" if effect['significant'] else "❌"
                        st.write(f"**{interaction}** {sig_marker}")
                        st.write(f"  F = {effect['f_statistic']:.4f}, p = {effect['p_value']:.4f}, η² = {effect['eta_squared']:.4f}")
                else:
                    st.info("No interactions analyzed (requires 2+ factors)")

    elif design_type == "Fractional Factorial Design (2^(k-p))":
        # Issue #8: Fractional Factorial UI Implementation
        st.header("Fractional Factorial Design (2^(k-p))")

        st.markdown("""
        <div class="info-box">
        <strong>What is Fractional Factorial?</strong><br>
        Screens many factors efficiently by testing a carefully selected FRACTION of all combinations.
        Perfect when you have 5+ factors and full factorial would require too many runs.
        <br><br>
        <strong>Example:</strong> Test 7 factors in only 16 runs (instead of 128 for full factorial!)
        <br><br>
        <strong>Resolution Levels:</strong>
        <ul>
            <li><strong>III:</strong> Main effects confounded with 2-way interactions (screening only)</li>
            <li><strong>IV:</strong> Main effects clear, 2-way interactions confounded (good)</li>
            <li><strong>V:</strong> Main and 2-way interactions clear (excellent)</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.subheader("Fractional Factorial Parameters")

        # Use pre-defined catalog or custom
        design_mode = st.sidebar.radio(
            "Design Mode",
            ["Common Designs (Recommended)", "Custom"],
            help=" Common Designs: Pre-optimized high-resolution designs. Custom: Specify your own parameters"
        )

        if design_mode == "Common Designs (Recommended)":
            design_options = {name: info['description'] for name, info in COMMON_DESIGNS.items()}

            selected_design = st.sidebar.selectbox(
                "Select Design",
                list(design_options.keys()),
                format_func=lambda x: design_options[x],
                help=" Pre-defined efficient designs with optimal resolution"
            )

            design_info = COMMON_DESIGNS[selected_design]
            n_factors = design_info['n_factors']
            n_runs = design_info['n_runs']
            generators = design_info['generators']
            resolution = design_info['resolution']

            st.sidebar.success(f"✅ **{n_factors} factors** in **{n_runs} runs**\n\nResolution **{resolution}**")

        else:  # Custom
            n_factors = st.sidebar.number_input(
                "Number of Factors",
                min_value=3,
                max_value=10,
                value=5,
                help=" Total number of factors to screen"
            )

            n_runs = st.sidebar.select_slider(
                "Number of Runs",
                options=[8, 16, 32, 64, 128],
                value=16,
                help=" Must be power of 2. Fewer runs = more aliasing"
            )

            generators = None  # Will use defaults

        factor_names = st.sidebar.text_input(
            "Factor Names (comma-separated)",
            value=", ".join([f"Factor_{chr(65+i)}" for i in range(n_factors)]),
            help=" Optional: Customize factor names"
        ).split(",")
        factor_names = [name.strip() for name in factor_names[:n_factors]]

        random_seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=9999, key="ffd_seed")

        # Create design
        if st.sidebar.button("Create Fractional Factorial", type="primary"):
            with st.spinner("Creating Fractional Factorial Design..."):
                ffd = FractionalFactorialDesign(random_seed=random_seed)

                design = ffd.create_design(
                    n_factors=n_factors,
                    n_runs=n_runs,
                    factor_names=factor_names if len(factor_names) == n_factors else None,
                    generators=generators if 'generators' in locals() else None,
                    randomize=True
                )

                st.session_state['current_design'] = design
                st.session_state['design_object'] = ffd
                st.session_state['design_type'] = 'Fractional_Factorial'

            st.success("✅ Fractional Factorial Design created!")

        # Display design
        if 'current_design' in st.session_state and st.session_state.get('design_type') == 'Fractional_Factorial':
            design = st.session_state['current_design']
            ffd = st.session_state['design_object']

            summary = ffd.get_design_summary()

            st.markdown("---")
            st.subheader(" Design Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Factors", summary['n_factors'])

            with col2:
                st.metric("Runs", summary['n_runs'])

            with col3:
                st.metric("Fraction", summary['fraction'])

            with col4:
                st.metric("Resolution", summary['resolution'])

            # Show efficiency gain
            full_factorial_runs = 2 ** summary['n_factors']
            efficiency = (1 - summary['n_runs'] / full_factorial_runs) * 100

            st.success(f" **Efficiency Gain:** {efficiency:.1f}% fewer runs than full factorial ({summary['n_runs']} vs {full_factorial_runs})")

            # Generators and alias structure
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Generators:**")
                for gen in summary['generators']:
                    st.code(gen)

            with col2:
                st.markdown("**Alias Structure (selected):**")
                alias_count = 0
                for effect, aliases in summary['alias_structure'].items():
                    if len(aliases) > 1 and alias_count < 5:
                        st.write(f"{effect} aliased with: {', '.join(aliases[1:])}")
                        alias_count += 1

            # Design matrix
            st.markdown("---")
            st.subheader("Design Matrix (Coded Units: -1, +1)")

            factor_cols = summary['factor_names']
            display_cols = factor_cols + ['std_order', 'run_order']
            st.dataframe(design[display_cols], width="stretch", height=400)

            # NEW: Assign design to sample units
            st.markdown("---")
            st.subheader(" Assign Design to ALL Sample Units")

            st.info("💡 Allocate all 20,000 customers across these treatment combinations")

            # Get unique treatment combinations (exclude replication/order columns)
            unique_combos = design[factor_cols].drop_duplicates().reset_index(drop=True)
            n_combos = len(unique_combos)

            st.write(f"**{n_combos} unique treatment combinations** in this design")

            allocation_mode = st.radio(
                "Allocation Method",
                ["Equal (same n per combination)", "Custom (specify per combination)"],
                key="ffd_allocation_mode"
            )

            if st.button(" Assign All Units to Design", key="ffd_assign"):
                np.random.seed(random_seed)

                # Assign all units to treatment combinations
                n_total = len(df)

                if allocation_mode == "Equal (same n per combination)":
                    # Equal allocation
                    base_size = n_total // n_combos
                    remainder = n_total % n_combos

                    assignments = []
                    for i in range(n_combos):
                        n_in_combo = base_size + (1 if i < remainder else 0)
                        assignments.extend([i] * n_in_combo)

                    np.random.shuffle(assignments)
                else:
                    # For now, use equal (custom can be added later if needed)
                    base_size = n_total // n_combos
                    remainder = n_total % n_combos
                    assignments = []
                    for i in range(n_combos):
                        n_in_combo = base_size + (1 if i < remainder else 0)
                        assignments.extend([i] * n_in_combo)
                    np.random.shuffle(assignments)

                # Assign treatment combinations
                df_assigned = df.copy()
                for i, factor in enumerate(factor_cols):
                    df_assigned[factor] = unique_combos.iloc[assignments][factor].values

                st.session_state['design_with_units'] = df_assigned

                st.success(f"✅ All {n_total:,} units assigned across {n_combos} treatment combinations!")

            # Display assigned design
            if 'design_with_units' in st.session_state and st.session_state.get('design_type') == 'Fractional_Factorial':
                assigned_design = st.session_state['design_with_units']

                st.subheader(" All Sample Units with Treatment Assignments")

                # Show allocation summary
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Units Assigned", f"{len(assigned_design):,}")

                with col2:
                    st.metric("Treatment Combinations", n_combos)

                with col3:
                    avg_per_combo = len(assigned_design) // n_combos
                    st.metric("Avg. per Combination", f"{avg_per_combo:,}")

                # Show distribution across combinations
                st.markdown("**Allocation Summary:**")
                allocation_summary = assigned_design[factor_cols].apply(
                    lambda row: ' | '.join([f"{col}={val}" for col, val in row.items()]), axis=1
                ).value_counts().reset_index()
                allocation_summary.columns = ['Treatment Combination', 'Count']

                st.dataframe(allocation_summary, width="stretch")

                # Show sample of assigned units
                st.markdown("---")
                st.markdown("**Sample Preview (First 20 Units):**")

                key_cols = ['customer_id', 'age', 'gender', 'income_level'] + factor_cols
                key_cols = [col for col in key_cols if col in assigned_design.columns]

                st.dataframe(assigned_design[key_cols].head(20), width="stretch")

                # Download assigned design
                csv_assigned = assigned_design.to_csv(index=False)
                st.download_button(
                    label=" Download All Units with Assignments",
                    data=csv_assigned,
                    file_name=f"fractional_factorial_assigned_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="ffd_download"
                )

    elif design_type == "Response Surface Method (CCD)":
        # Issue #8: Central Composite Design UI
        st.header("Central Composite Design (CCD)")

        st.markdown("""
        <div class="info-box">
        <strong>What is CCD?</strong><br>
        After screening identifies important factors, CCD finds OPTIMAL settings by fitting
        a quadratic response surface model. Can detect curvature and find peaks/valleys.
        <br><br>
        <strong>Components:</strong> Factorial points + Axial points + Center points
        <br>
        <strong>When to use:</strong> 2-5 key factors, seeking optimization
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.subheader("CCD Parameters")

        n_factors = st.sidebar.number_input(
            "Number of Factors",
            min_value=2,
            max_value=5,
            value=3,
            help=" Number of factors to optimize (2-5 recommended)"
        )

        ccd_type = st.sidebar.selectbox(
            "CCD Type",
            ["Rotatable", "Face-Centered", "Orthogonal"],
            help=" Rotatable: Equal prediction variance. Face-Centered: Factors stay within [-1,1]. Orthogonal: Orthogonal estimates"
        )

        n_center = st.sidebar.slider(
            "Center Points",
            min_value=3,
            max_value=10,
            value=5,
            help=" Replicated center points for pure error estimation. 3-6 recommended"
        )

        factor_names = st.sidebar.text_input(
            "Factor Names (comma-separated)",
            value=", ".join([f"Factor_{i+1}" for i in range(n_factors)]),
            key="ccd_factors"
        ).split(",")
        factor_names = [name.strip() for name in factor_names[:n_factors]]

        random_seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=9999, key="ccd_seed")

        if st.sidebar.button(" Create CCD", type="primary"):
            with st.spinner("Creating Central Composite Design..."):
                ccd = CentralCompositeDesign(random_seed=random_seed)

                design = ccd.create_design(
                    n_factors=n_factors,
                    design_type=ccd_type.lower().replace('-', '_'),
                    n_center_points=n_center,
                    factor_names=factor_names if len(factor_names) == n_factors else None,
                    randomize=True
                )

                st.session_state['current_design'] = design
                st.session_state['design_object'] = ccd
                st.session_state['design_type'] = 'CCD'

            st.success(" Central Composite Design created!")

        # Display design
        if 'current_design' in st.session_state and st.session_state.get('design_type') == 'CCD':
            design = st.session_state['current_design']
            ccd = st.session_state['design_object']
            summary = ccd.get_design_summary()

            st.markdown("---")
            st.subheader(" Design Summary")

            col1, col2, col3, col4, col5 = st.columns(5)

            with col1:
                st.metric("Factors", summary['n_factors'])

            with col2:
                st.metric("Factorial Points", summary['n_factorial_points'])

            with col3:
                st.metric("Axial Points", summary['n_axial_points'])

            with col4:
                st.metric("Center Points", summary['n_center_points'])

            with col5:
                st.metric("Total Runs", summary['total_runs'])

            st.info(f" Alpha (axial distance): {summary['alpha']:.3f} | Rotatability: {summary['rotatability']}")

            # Design matrix
            st.markdown("---")
            st.subheader("Design Matrix (Coded Units)")

            # Color-code by point type
            st.dataframe(design, width="stretch", height=400)

            # NEW: Assign design to sample units for CCD
            st.markdown("---")
            st.subheader(" Assign Design to ALL Sample Units")

            st.info(" Allocate all 20,000 customers across these treatment combinations")

            # Get unique treatment combinations (exclude point_type, replication, order columns)
            unique_combos = design[summary['factor_names']].drop_duplicates().reset_index(drop=True)
            n_combos = len(unique_combos)

            st.write(f"**{n_combos} unique treatment combinations** (factorial + axial + center points)")

            if st.button(" Assign All Units to Design", key="ccd_assign"):
                np.random.seed(random_seed)

                # Assign all units to treatment combinations
                n_total = len(df)
                base_size = n_total // n_combos
                remainder = n_total % n_combos

                assignments = []
                for i in range(n_combos):
                    n_in_combo = base_size + (1 if i < remainder else 0)
                    assignments.extend([i] * n_in_combo)

                np.random.shuffle(assignments)

                # Assign treatment combinations
                df_assigned = df.copy()
                for factor in summary['factor_names']:
                    df_assigned[factor] = unique_combos.iloc[assignments][factor].values

                st.session_state['design_with_units'] = df_assigned

                st.success(f"✅ All {n_total:,} units assigned across {n_combos} treatment combinations!")

            # Display assigned design
            if 'design_with_units' in st.session_state and st.session_state.get('design_type') == 'CCD':
                assigned_design = st.session_state['design_with_units']

                st.subheader(" All Sample Units with Treatment Assignments")

                # Show allocation summary
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Units Assigned", f"{len(assigned_design):,}")

                with col2:
                    st.metric("Treatment Combinations", n_combos)

                with col3:
                    avg_per_combo = len(assigned_design) // n_combos
                    st.metric("Avg. per Combination", f"{avg_per_combo:,}")

                # Show distribution across combinations
                st.markdown("**Allocation Summary:**")
                allocation_summary = assigned_design[summary['factor_names']].apply(
                    lambda row: ' | '.join([f"{col}={val:.2f}" for col, val in row.items()]), axis=1
                ).value_counts().reset_index()
                allocation_summary.columns = ['Treatment Combination', 'Count']

                st.dataframe(allocation_summary, width="stretch")

                # Show sample of assigned units
                st.markdown("---")
                st.markdown("**Sample Preview (First 20 Units):**")

                key_cols = ['customer_id', 'age', 'gender', 'income_level'] + summary['factor_names']
                key_cols = [col for col in key_cols if col in assigned_design.columns]

                st.dataframe(assigned_design[key_cols].head(20), width="stretch")

                # Download assigned design
                csv_assigned = assigned_design.to_csv(index=False)
                st.download_button(
                    label=" Download All Units with Assignments",
                    data=csv_assigned,
                    file_name=f"ccd_assigned_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="ccd_download"
                )

    elif design_type == "Box-Behnken Design":
        # Issue #8: Box-Behnken Design UI
        st.header("Box-Behnken Design")

        st.markdown("""
        <div class="info-box">
        <strong>What is Box-Behnken?</strong><br>
        A 3-level response surface design that AVOIDS extreme corner points.
        Safer when extreme factor combinations are dangerous, expensive, or impractical.
        <br><br>
        <strong>Advantage:</strong> Usually requires fewer runs than CCD for 3+ factors
        <br>
        <strong>When to use:</strong> Extreme combinations unsafe or process operates in interior only
        </div>
        """, unsafe_allow_html=True)

        st.sidebar.subheader("Box-Behnken Parameters")

        n_factors = st.sidebar.number_input(
            "Number of Factors",
            min_value=3,
            max_value=7,
            value=3,
            help=" Number of factors (requires at least 3)"
        )

        n_center = st.sidebar.slider(
            "Center Points",
            min_value=3,
            max_value=10,
            value=3,
            help=" Center point replicates for pure error",
            key="bbd_center"
        )

        factor_names = st.sidebar.text_input(
            "Factor Names (comma-separated)",
            value=", ".join([f"Factor_{i+1}" for i in range(n_factors)]),
            key="bbd_factors"
        ).split(",")
        factor_names = [name.strip() for name in factor_names[:n_factors]]

        random_seed = st.sidebar.number_input("Random Seed", value=42, min_value=0, max_value=9999, key="bbd_seed")

        if st.sidebar.button(" Create Box-Behnken", type="primary"):
            with st.spinner("Creating Box-Behnken Design..."):
                bbd = BoxBehnkenDesign(random_seed=random_seed)

                design = bbd.create_design(
                    n_factors=n_factors,
                    n_center_points=n_center,
                    factor_names=factor_names if len(factor_names) == n_factors else None,
                    randomize=True
                )

                st.session_state['current_design'] = design
                st.session_state['design_object'] = bbd
                st.session_state['design_type'] = 'BBD'

            st.success("✅ Box-Behnken Design created!")

        # Display design
        if 'current_design' in st.session_state and st.session_state.get('design_type') == 'BBD':
            design = st.session_state['current_design']
            bbd = st.session_state['design_object']
            summary = bbd.get_design_summary()

            st.markdown("---")
            st.subheader(" Design Summary")

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Factors", summary['n_factors'])

            with col2:
                st.metric("Edge Points", summary['n_edge_points'])

            with col3:
                st.metric("Center Points", summary['n_center_points'])

            with col4:
                st.metric("Total Runs", summary['total_runs'])

            st.success("✅ Avoids extreme corners - safer for process boundaries!")

            # Design matrix
            st.markdown("---")
            st.subheader("Design Matrix (Coded Units: -1, 0, +1)")

            st.dataframe(design, width="stretch", height=400)

            # NEW: Assign design to sample units for Box-Behnken
            st.markdown("---")
            st.subheader(" Assign Design to ALL Sample Units")

            st.info(" Allocate all 20,000 customers across these treatment combinations")

            # Get unique treatment combinations (exclude point_type, order columns)
            unique_combos = design[summary['factor_names']].drop_duplicates().reset_index(drop=True)
            n_combos = len(unique_combos)

            st.write(f"**{n_combos} unique treatment combinations** (edge + center points)")

            if st.button(" Assign All Units to Design", key="bbd_assign"):
                np.random.seed(random_seed)

                # Assign all units to treatment combinations
                n_total = len(df)
                base_size = n_total // n_combos
                remainder = n_total % n_combos

                assignments = []
                for i in range(n_combos):
                    n_in_combo = base_size + (1 if i < remainder else 0)
                    assignments.extend([i] * n_in_combo)

                np.random.shuffle(assignments)

                # Assign treatment combinations
                df_assigned = df.copy()
                for factor in summary['factor_names']:
                    df_assigned[factor] = unique_combos.iloc[assignments][factor].values

                st.session_state['design_with_units'] = df_assigned

                st.success(f"✅ All {n_total:,} units assigned across {n_combos} treatment combinations!")

            # Display assigned design
            if 'design_with_units' in st.session_state and st.session_state.get('design_type') == 'BBD':
                assigned_design = st.session_state['design_with_units']

                st.subheader(" All Sample Units with Treatment Assignments")

                # Show allocation summary
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.metric("Total Units Assigned", f"{len(assigned_design):,}")

                with col2:
                    st.metric("Treatment Combinations", n_combos)

                with col3:
                    avg_per_combo = len(assigned_design) // n_combos
                    st.metric("Avg. per Combination", f"{avg_per_combo:,}")

                # Show distribution across combinations
                st.markdown("**Allocation Summary:**")
                allocation_summary = assigned_design[summary['factor_names']].apply(
                    lambda row: ' | '.join([f"{col}={val:.1f}" for col, val in row.items()]), axis=1
                ).value_counts().reset_index()
                allocation_summary.columns = ['Treatment Combination', 'Count']

                st.dataframe(allocation_summary, width="stretch")

                # Show sample of assigned units
                st.markdown("---")
                st.markdown("**Sample Preview (First 20 Units):**")

                key_cols = ['customer_id', 'age', 'gender', 'income_level'] + summary['factor_names']
                key_cols = [col for col in key_cols if col in assigned_design.columns]

                st.dataframe(assigned_design[key_cols].head(20), width="stretch")

                # Download assigned design
                csv_assigned = assigned_design.to_csv(index=False)
                st.download_button(
                    label=" Download All Units with Assignments",
                    data=csv_assigned,
                    file_name=f"box_behnken_assigned_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    key="bbd_download"
                )

    # Issue #7 FIX: Enhanced export with treatment assignments and metadata
    if 'current_design' in st.session_state:
        st.markdown("---")
        st.header(" Export Design & Assignments")

        design = st.session_state['current_design']
        design_type_label = st.session_state.get('design_type', 'experiment')

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("###  Design Matrix")

            csv = design.to_csv(index=False)
            st.download_button(
                label=" Download Design Matrix (CSV)",
                data=csv,
                file_name=f"design_{design_type_label}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                width="stretch",
                help="Downloads the complete design matrix with all factor levels and run orders"
            )

            st.info(f" Includes: {len(design)} runs with all factor assignments")

        with col2:
            st.markdown("###  Design Info")

            # Create metadata file
            if 'design_object' in st.session_state:
                design_obj = st.session_state['design_object']
                summary = design_obj.get_design_summary()

                # Format summary as readable text
                metadata_text = f"""Design Type: {summary.get('design_type', design_type_label)}
Created: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Runs: {len(design)}
Random Seed: {summary.get('random_seed', 'N/A')}

Design Parameters:
{chr(10).join([f'  {k}: {v}' for k, v in summary.items() if k not in ['design_type', 'random_seed']])}
"""

                st.download_button(
                    label="📄 Download Design Info (TXT)",
                    data=metadata_text,
                    file_name=f"design_info_{design_type_label}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain",
                    width="stretch",
                    help="Downloads design metadata including parameters and configuration"
                )

                st.info(" Includes: Full design specifications")

        # Show preview
        st.markdown("---")
        st.subheader(" Design Preview")

        st.dataframe(design.head(20), width="stretch")

        st.caption(f"Showing first 20 of {len(design)} total runs")

else:
    st.error("Failed to load dataset.")
