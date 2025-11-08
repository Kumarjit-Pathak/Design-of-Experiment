"""
DOE Simulator - Streamlit Multi-Page Application

Main entry point for the Design of Experiments interactive simulator.
This app demonstrates sampling methods, experimental designs, and diagnostics
using realistic e-commerce data.

Author: DOE Simulator Team
"""

import streamlit as st
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page configuration
st.set_page_config(
    page_title="DOE Simulator",
    page_icon="🎲",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/your-repo/DOE_Simulator',
        'Report a bug': 'https://github.com/your-repo/DOE_Simulator/issues',
        'About': """
        # DOE Simulator

        An interactive tool for learning and applying Design of Experiments techniques.

        **Features:**
        - Multiple sampling methods
        - Balance checking
        - Statistical tests
        - Interactive visualizations

        Built with Streamlit and love for statistics! 📊
        """
    }
)

# Custom CSS - SLATE PROFESSIONAL THEME (Tailwind-inspired)
st.markdown("""
<style>
    /* Main background - Slate gradient */
    .main {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        color: #cbd5e1;
    }

    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #38bdf8;
        text-align: center;
        padding: 1rem 0;
        text-shadow: 0 0 20px rgba(56, 189, 248, 0.4);
    }

    .sub-header {
        font-size: 1.5rem;
        color: #facc15;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 0 0 15px rgba(250, 204, 21, 0.3);
    }

    /* Highlight box - Slate with sky blue border */
    .highlight-box {
        background: linear-gradient(135deg, #334155 0%, #475569 100%);
        border: 2px solid #38bdf8;
        color: #facc15;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
    }

    .highlight-box h3 {
        color: #38bdf8;
        margin-top: 0;
    }

    .highlight-box p {
        color: #cbd5e1;
    }

    /* Info box */
    .info-box {
        background-color: #334155;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #38bdf8;
        margin: 1rem 0;
        color: #cbd5e1;
    }

    .info-box h4 {
        color: #38bdf8;
    }

    /* Success box */
    .success-box {
        background-color: #1e3a2e;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #4ade80;
        margin: 1rem 0;
        color: #cbd5e1;
    }

    /* Warning box */
    .warning-box {
        background-color: #3a3020;
        padding: 1rem;
        border-radius: 5px;
        border-left: 5px solid #facc15;
        margin: 1rem 0;
        color: #cbd5e1;
    }

    /* Buttons - Sky blue with hover to yellow */
    .stButton>button {
        background-color: #38bdf8;
        color: #1e293b;
        font-weight: bold;
        border-radius: 6px;
        padding: 0.6rem 2rem;
        border: 2px solid #38bdf8;
        transition: all 0.3s ease;
    }

    .stButton>button:hover {
        background-color: #facc15;
        border-color: #facc15;
        color: #1e293b;
        box-shadow: 0 0 20px rgba(250, 204, 21, 0.5);
        transform: translateY(-2px);
    }

    /* Sidebar - Darker slate */
    [data-testid="stSidebar"] {
        background-color: #1e293b;
        border-right: 1px solid #334155;
    }

    /* Fix sidebar navigation text visibility - Issue #9 */
    [data-testid="stSidebar"] .css-1544g2n,
    [data-testid="stSidebar"] a,
    [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
        color: #e2e8f0 !important;
        font-weight: 500 !important;
    }

    [data-testid="stSidebar"] a:hover {
        color: #38bdf8 !important;
    }

    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {
        color: #38bdf8;
    }

    /* Metrics - Sky blue values, slate gray labels */
    [data-testid="stMetricValue"] {
        color: #38bdf8;
        font-weight: bold;
        font-size: 1.8rem;
    }

    [data-testid="stMetricLabel"] {
        color: #94a3b8;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Headers - Sky blue */
    h1, h2, h3 {
        color: #38bdf8;
    }

    h4, h5, h6 {
        color: #facc15;
    }

    /* Text */
    p, li, span {
        color: #cbd5e1;
    }

    /* Dataframes */
    .dataframe {
        background-color: #334155;
        color: #cbd5e1;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #1e293b;
    }

    .stTabs [data-baseweb="tab"] {
        color: #94a3b8;
    }

    .stTabs [aria-selected="true"] {
        color: #38bdf8;
        border-bottom-color: #38bdf8;
    }

    /* Selectbox, inputs */
    .stSelectbox, .stMultiSelect, .stNumberInput {
        color: #cbd5e1;
    }

    /* Footer text */
    .footer-text {
        color: #64748b;
        text-align: center;
    }

    /* Success/Warning/Error messages */
    .element-container .stSuccess {
        background-color: #1e3a2e;
        color: #4ade80;
    }

    .element-container .stWarning {
        background-color: #3a3020;
        color: #facc15;
    }

    .element-container .stError {
        background-color: #3a1e1e;
        color: #f87171;
    }

    .element-container .stInfo {
        background-color: #1e2a3a;
        color: #38bdf8;
    }
</style>
""", unsafe_allow_html=True)

# Main page content
def main():
    """Main landing page."""

    # Header
    st.markdown('<p class="main-header">🎲 DOE Simulator</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Design of Experiments Made Interactive</p>', unsafe_allow_html=True)

    # Welcome message
    st.markdown("""
    <div class="highlight-box">
        <h3>Welcome to the DOE Simulator!</h3>
        <p>An interactive tool for learning and applying Design of Experiments techniques using realistic e-commerce data.</p>
    </div>
    """, unsafe_allow_html=True)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Dataset Size", "20,000 rows", "24 features")

    with col2:
        st.metric("Sampling Methods", "4", "Fully implemented")

    with col3:
        st.metric("Balance Checking", "✓", "SMD + Tests")

    with col4:
        st.metric("Visualizations", "Coming Soon", "Interactive plots")

    st.markdown("---")

    # Features
    st.header("🎯 What You Can Do")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 📊 Available Now

        ✅ **Data Exploration**
        - View 20,000 e-commerce customer records
        - Explore feature distributions
        - Check data quality

        ✅ **Sampling Methods**
        - Simple Random Sampling
        - Stratified Sampling (with efficiency calculations!)
        - Systematic Sampling (with periodicity detection)
        - Cluster Sampling (with ICC & design effects)

        ✅ **Balance Checking**
        - Treatment-control balance assessment
        - Standardized mean differences (SMD)
        - Statistical tests (t-test, chi-square)
        - Overall balance scoring
        - Love plot data preparation
        """)

    with col2:
        st.markdown("""
        ### 🚀 Coming Soon

        ⏳ **Advanced Visualizations**
        - Love plots (standardized differences)
        - Box plots & violin plots
        - Q-Q plots & residual analysis
        - Interactive dashboards

        ⏳ **Experimental Designs**
        - Completely Randomized Design (CRD)
        - Randomized Block Design (RBD)
        - Factorial Designs
        - Response Surface Methods
        - Optimal Designs

        ⏳ **Power Analysis**
        - Sample size calculations
        - Minimum detectable effects
        """)

    st.markdown("---")

    # Quick start guide
    st.header("🚀 Quick Start")

    st.markdown("""
    <div class="info-box">
    <h4>New to Design of Experiments?</h4>
    <ol>
        <li><strong>Start with Data Explorer</strong> - Understand the dataset</li>
        <li><strong>Try Sampling Methods</strong> - See how different methods work</li>
        <li><strong>Check Balance</strong> - Learn about treatment-control balance</li>
        <li><strong>Experiment!</strong> - Play with different settings</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)

    # Navigation
    st.header("📍 Navigate")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 Explore Data", width="stretch"):
            st.info("👈 Use the sidebar to navigate to 'Data Explorer'")

    with col2:
        if st.button("🎲 Try Sampling", width="stretch"):
            st.info("👈 Use the sidebar to navigate to 'Sampling Methods'")

    with col3:
        if st.button("✅ Check Balance", width="stretch"):
            st.info("👈 Use the sidebar to navigate to 'Balance Checker'")

    st.markdown("---")

    # Footer
    st.markdown("""
    <div style="text-align: center; padding: 2rem 0; color: #666;">
        <p><strong>DOE Simulator v1.0</strong></p>
        <p>Built with Streamlit • Python • Statistics • Love for Data 📊</p>
        <p><em>Because guessing is SO last century</em> 🎲</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
