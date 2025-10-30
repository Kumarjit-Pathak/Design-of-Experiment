# DOE Simulator - Design of Experiments Interactive Tool

## Project Overview

An interactive web-based simulator for learning and applying Design of Experiments (DOE) techniques using realistic e-commerce customer data. This tool demonstrates various sampling methods, experimental designs, and diagnostic checks with comprehensive visualizations and statistical validations.

---

## Features

- ✅ **20,000-row realistic e-commerce dataset** with diverse customer characteristics
- 📊 **Multiple sampling methods:** Simple random, stratified, systematic, cluster
- 🔬 **Experimental design techniques:** CRD, RBD, factorial, fractional factorial, response surface, optimal designs
- 🎯 **Comprehensive diagnostics:** Balance checking, power analysis, assumption validation
- 📈 **Interactive visualizations:** Love plots, box plots, violin plots, Q-Q plots
- 🎨 **Web-based interface:** Streamlit app for easy experimentation
- 📚 **Educational content:** Learn DOE concepts interactively

---

## Project Status

### ✅ Phase 1: Data Generation (COMPLETED)

**Deliverables:**
- [x] Project folder structure created
- [x] Data generator script (`data/data_generator.py`)
- [x] 20,000-row e-commerce dataset (`data/raw/ecommerce_data.csv`)
- [x] Data validation script (`data/validate_data.py`)
- [x] Comprehensive dataset documentation (`docs/DATASET_DOCUMENTATION.md`)

**Dataset Highlights:**
- **Size:** 20,000 customers × 24 features
- **Categories:** Demographics, shopping behavior, engagement, behavioral indicators, target variables
- **Correlations:** Realistic patterns (income↔order value, orders↔lifetime value, etc.)
- **Missing Data:** 5% MCAR in 5 selected columns
- **Validation:** All checks passed ✓

### ✅ Phase 2: Modular Python Scripts (PARTIALLY COMPLETED)
- [x] ✅ **Utility modules (3 scripts)** - config_loader, data_loader, statistical_tests
- [x] ✅ **Sampling methods (4 scripts)** - Simple, Stratified, Systematic, Cluster
- [x] ✅ **Balance checker (1 critical script)** - Treatment-control balance, SMD, Love plot data
- [ ] 🚧 Diagnostic modules (2 remaining) - power_analysis, assumption_checks
- [ ] 🚧 Visualization modules (3 scripts) - balance_plots, diagnostic_plots, summary_visuals
- [ ] 🚧 Experimental designs (6 scripts) - CRD, RBD, factorial, etc.

**Status:** 8 of 19 modules complete (~3,600 lines of code)

### ✅ Phase 3: Interactive Streamlit App (COMPLETED - MVP)
- [x] ✅ **Main app structure** (`streamlit_app.py`)
- [x] ✅ **Home page** - Welcome, navigation, quick start
- [x] ✅ **Data Explorer page** - Interactive data exploration, filters, distributions, correlations
- [x] ✅ **Sampling Methods page** - All 4 methods interactive
- [x] ✅ **Balance Checker page** - Treatment assignment, balance checking, Love plot data
- [x] ✅ **Requirements.txt** - All dependencies listed
- [x] ✅ **Launch guide** - Step-by-step instructions

**Status:** MVP Ready! Fully functional demo with core features.

### 🔄 Phase 4: Enhancement & Polish (PENDING)
- [ ] Complete remaining diagnostic modules
- [ ] Add experimental design pages
- [ ] Enhanced visualizations (interactive Love plots)
- [ ] Unit tests
- [ ] User guide
- [ ] Example notebooks

### 🔄 Phase 5: Deployment (PENDING)
- [ ] GitHub repository setup
- [ ] Streamlit Cloud deployment
- [ ] Documentation hosting
- [ ] Demo video

---

## 🚀 Quick Start - Launch the App!

### 1. Install Dependencies

```bash
cd DOE_Simulator
pip install -r requirements.txt
```

### 2. Launch Streamlit App

```bash
cd app
streamlit run streamlit_app.py
```

The app opens at `http://localhost:8501` 🎉

**Available Pages:**
- 📊 **Data Explorer** - 20K customers, interactive filters, distributions, correlations
- 🎲 **Sampling Methods** - All 4 methods (Simple, Stratified, Systematic, Cluster)
- ✅ **Balance Checker** - Treatment-control balance, SMD, Love plot data

---

## Quick Start - Python Scripts

### Use Sampling Methods

```python
from src.sampling import simple_random_sampling, stratified_sampling

# Simple random sample
sample = simple_random_sampling.run({
    'data_path': 'data/raw/ecommerce_data.csv',
    'sample_size': 1000
})

# Stratified sample (shows 6.56% efficiency gain!)
sample = stratified_sampling.run({
    'data_path': 'data/raw/ecommerce_data.csv',
    'stratify_by': 'income_level',
    'sample_size': 1000
})
```

### Check Balance

```python
from src.diagnostics.balance_checker import BalanceChecker

checker = BalanceChecker(df, treatment_col='treatment')
results = checker.check_balance(['age', 'gender', 'income'])

# Balance score
print(f"Score: {results['overall_balance']['balance_percentage']:.1f}%")
```

---

## Dataset Features

### Demographics (5 features)
- `customer_id`: Unique identifier
- `age`: 18-75 years
- `gender`: Male, Female, Non-binary
- `location`: Urban, Suburban, Rural
- `income_level`: Low, Medium, High, Very High
- `education`: High School, Bachelor, Master, PhD

### Shopping Behavior (5 features)
- `account_age_days`: Days since registration
- `total_orders`: Historical order count
- `avg_order_value`: Average order value (USD)
- `last_order_days_ago`: Days since last purchase
- `product_category_preference`: Electronics, Fashion, Home, Books, Sports

### Engagement Metrics (5 features)
- `email_open_rate`: Email engagement (%)
- `website_visits_per_month`: Monthly site visits
- `mobile_app_user`: Yes/No
- `loyalty_program_member`: Yes/No
- `customer_service_interactions`: Contact count

### Behavioral Indicators (4 features)
- `cart_abandonment_rate`: Abandoned carts (%)
- `review_count`: Number of reviews written
- `avg_rating_given`: Average star rating (1-5)
- `social_media_follower`: Yes/No

### Target Variables (4 features)
- `conversion_rate`: Predicted conversion probability (%)
- `lifetime_value`: Customer lifetime value (USD)
- `churn_probability`: Predicted churn risk (%)
- `response_to_marketing`: Binary response (0/1)

📖 **Full Documentation:** See `docs/DATASET_DOCUMENTATION.md`

---

## Folder Structure

```
DOE_Simulator/
│
├── README.md                          # This file
├── IMPLEMENTATION_PLAN.md             # Detailed project plan
├── requirements.txt                   # Python dependencies (TBD)
├── config.json                        # Configuration file (TBD)
│
├── data/
│   ├── raw/
│   │   └── ecommerce_data.csv        # Generated dataset ✓
│   ├── processed/                    # Processed datasets (TBD)
│   ├── data_generator.py             # Data generation script ✓
│   └── validate_data.py              # Validation script ✓
│
├── src/                              # Source code (TBD - Phase 2)
│   ├── sampling/                     # Sampling methods
│   ├── experimental_designs/         # Experimental designs
│   ├── diagnostics/                  # Diagnostic checks
│   ├── visualization/                # Visualization modules
│   └── utils/                        # Utilities
│
├── app/                              # Streamlit app (TBD - Phase 3)
│   ├── streamlit_app.py
│   └── pages/
│
├── tests/                            # Unit tests (TBD - Phase 4)
├── notebooks/                        # Jupyter notebooks (TBD)
└── docs/
    └── DATASET_DOCUMENTATION.md      # Dataset documentation ✓
```

---

## Technology Stack

- **Python 3.8+**
- **pandas & numpy** - Data manipulation
- **scipy & statsmodels** - Statistical analysis
- **plotly & matplotlib** - Visualizations
- **streamlit** - Web application
- **scikit-learn** - Machine learning utilities

---

## Installation (Coming in Phase 2)

```bash
# Clone repository
git clone https://github.com/[your-repo]/DOE_Simulator.git
cd DOE_Simulator

# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run app/streamlit_app.py
```

---

## Usage Examples (Coming in Phase 2)

### Example 1: Simple Random Sampling

```python
from src.sampling import simple_random_sampling

config = {
    "data_path": "data/raw/ecommerce_data.csv",
    "sample_size": 1000,
    "random_seed": 42
}

sample = simple_random_sampling.run(config)
print(f"Sample size: {len(sample)}")
```

### Example 2: Stratified Sampling

```python
from src.sampling import stratified_sampling

config = {
    "data_path": "data/raw/ecommerce_data.csv",
    "sample_size": 1000,
    "stratify_by": "income_level",
    "random_seed": 42
}

sample = stratified_sampling.run(config)
```

### Example 3: Balance Checking

```python
from src.diagnostics import balance_checker

results = balance_checker.check_balance(
    data=sample,
    treatment_col="treatment_group",
    balance_cols=["age", "gender", "income_level", "total_orders"]
)

results.summary()  # Display balance metrics
results.plot_love()  # Create Love plot
```

---

## Development Roadmap

### Phase 1: Data Generation ✅ COMPLETED
- Duration: 1 week
- Status: ✅ Complete
- Deliverables: Dataset, validation, documentation

### Phase 2: Core Implementation 🔄 NEXT
- Duration: 2 weeks
- Status: ⏳ Pending
- Focus: Sampling methods, designs, diagnostics, visualization

### Phase 3: Web Application
- Duration: 1 week
- Status: ⏳ Pending
- Focus: Streamlit multi-page app

### Phase 4: Testing & Documentation
- Duration: 1 week
- Status: ⏳ Pending
- Focus: Tests, guides, examples

### Phase 5: Deployment
- Duration: 3 days
- Status: ⏳ Pending
- Focus: GitHub, Streamlit Cloud, documentation site

---

## Contributing

This is an educational project. Contributions welcome!

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## License

MIT License - See LICENSE file for details

---

## Acknowledgments

- Inspired by classical DOE literature (Fisher, Box, Taguchi)
- Built for educational purposes
- Dataset generated synthetically for demonstration

---

## Contact

- **Project Lead:** DOE Simulator Team
- **Repository:** https://github.com/[your-repo]/DOE_Simulator
- **Issues:** Use GitHub issue tracker

---

**Last Updated:** 2025-01-15
**Project Version:** 0.1.0 (Phase 1 Complete)
**Next Milestone:** Phase 2 - Core Implementation
