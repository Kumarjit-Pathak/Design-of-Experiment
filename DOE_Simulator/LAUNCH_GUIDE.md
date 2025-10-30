# 🚀 DOE Simulator - Launch Guide

## Quick Start

### 1. Install Dependencies

```bash
# Navigate to project directory
cd DOE_Simulator

# Install required packages
pip install -r requirements.txt
```

### 2. Launch the Streamlit App

```bash
# From the project root directory
cd app
streamlit run streamlit_app.py
```

The app will automatically open in your default browser at `http://localhost:8501`

---

## 📱 Using the App

### Home Page
- Overview of features
- Quick navigation
- Getting started guide

### Data Explorer 📊
- View 20,000 customer records
- Explore distributions
- Check correlations
- Analyze missing data
- **Interactive filters** (income, location, gender)

### Sampling Methods 🎲
- **Simple Random Sampling** - Equal probability selection
- **Stratified Sampling** - Stratify by income/location/gender/education
  - Proportional or equal allocation
  - See efficiency gains!
- **Systematic Sampling** - Every kth element
  - Periodicity detection included
- **Cluster Sampling** - Select clusters and sample within
  - ICC calculations
  - Design effect warnings

### Balance Checker ✅
- **Create random treatment assignments** or use existing columns
- Select covariates to check
- Get **balance scores** (0-100%)
- View **Love plot data** (SMD visualization)
- See detailed balance metrics
- Get **recommendations** for adjustment

---

## 🎯 Example Workflow

### Scenario: Test a marketing campaign

1. **Explore Data** (Data Explorer)
   - Understand customer characteristics
   - Check feature distributions
   - Identify key variables

2. **Create Sample** (Sampling Methods)
   - Use stratified sampling by income_level
   - Set sample size to 2,000
   - Choose proportional allocation
   - **Result:** 6.56% efficiency gain over simple random sampling!

3. **Assign Treatment** (Balance Checker)
   - Create 50-50 treatment-control split
   - Check balance on: age, gender, income, total_orders
   - **Goal:** Balance score >90% (Excellent)

4. **Check Balance**
   - View standardized mean differences (SMD)
   - Ensure |SMD| < 0.1 for all covariates
   - View Love plot data
   - If imbalanced → consider adjustment methods

5. **Download Results**
   - Export sample as CSV
   - Use for further analysis

---

## 📊 Features Available NOW

### ✅ Working Features

**Data Exploration:**
- ✅ 20,000-row dataset
- ✅ 24 features across 5 categories
- ✅ Interactive filters
- ✅ Distribution plots
- ✅ Correlation analysis
- ✅ Missing data analysis

**Sampling:**
- ✅ 4 complete methods (Simple, Stratified, Systematic, Cluster)
- ✅ Efficiency calculations
- ✅ Representativeness checks
- ✅ Periodicity detection
- ✅ ICC & design effects
- ✅ CSV download

**Balance Checking:**
- ✅ Random treatment assignment
- ✅ SMD calculations
- ✅ Statistical tests (t-test, chi-square)
- ✅ Overall balance scoring
- ✅ Love plot data preparation
- ✅ Traffic light system (🟢🟡🟠🔴)
- ✅ Recommendations

### 🚧 Coming Soon

**Visualizations:**
- Love plot interactive visualization
- Box plots & violin plots
- Q-Q plots
- Residual analysis

**Experimental Designs:**
- Completely Randomized Design
- Randomized Block Design
- Factorial designs
- Response surface methods

**Advanced:**
- Power analysis
- Propensity score matching
- ANCOVA adjustments

---

## 🎓 Tips for Best Results

### Sampling Methods

1. **Start with Simple Random** - Understand baseline
2. **Try Stratified** - See efficiency gains (often 5-10%!)
3. **Check Systematic** - But watch for periodicity warnings
4. **Use Cluster** - When logistically convenient, but monitor ICC

### Balance Checking

1. **Always check balance** before analyzing treatment effects
2. **Aim for |SMD| < 0.1** on all important covariates
3. **Focus on effect sizes**, not just p-values
4. **If balance score < 70%** → consider:
   - Re-randomization
   - Stratified randomization
   - Covariate adjustment (ANCOVA)
   - Propensity scores

### General

1. **Set random seed** for reproducibility
2. **Download samples** for records
3. **Document decisions** (what covariates, why)
4. **Iterate** - try different approaches

---

## 🐛 Troubleshooting

### App won't start
```bash
# Make sure you're in the app directory
cd DOE_Simulator/app
streamlit run streamlit_app.py
```

### Import errors
```bash
# Reinstall requirements
pip install -r requirements.txt --upgrade
```

### Data not loading
- Check that `data/raw/ecommerce_data.csv` exists
- Run `python data/data_generator.py` to regenerate if needed

### Plots not showing
- Update plotly: `pip install plotly --upgrade`
- Clear browser cache
- Try different browser

---

## 💻 System Requirements

- **Python:** 3.8 or higher
- **RAM:** 4GB minimum (8GB recommended)
- **Storage:** ~500MB for app + dependencies
- **Browser:** Chrome, Firefox, Edge, or Safari (latest versions)

---

## 📝 Notes

### Path Issues
If you encounter path issues, ensure you're running from the correct directory:
```bash
# Should see these folders:
DOE_Simulator/
├── app/           # Run streamlit from here
├── data/          # Dataset location
├── src/           # Source code
└── config/        # Configuration files
```

### Performance
- **First load:** May take 10-15 seconds
- **Subsequent loads:** Cached, much faster (<1 second)
- **Large samples:** >5000 may slow down slightly

### Data Persistence
- Samples stored in session state (lost on refresh)
- **Always download** important samples as CSV

---

## 🎉 You're Ready!

Launch the app and start exploring Design of Experiments interactively!

```bash
cd app
streamlit run streamlit_app.py
```

Enjoy! 📊🎲✅

---

## 📧 Support

- **Issues:** Create GitHub issue
- **Questions:** Check documentation in `docs/`
- **Updates:** Pull latest from repository

**Happy Experimenting!** 🚀
