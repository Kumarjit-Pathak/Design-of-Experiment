# E-commerce Customer Dataset Documentation

## Overview

This dataset contains 20,000 simulated e-commerce customer records designed for demonstrating Design of Experiments (DOE) techniques. The data includes realistic patterns, correlations, and missing data to mimic real-world scenarios.

**Dataset Size:** 20,000 rows × 24 columns
**File Size:** ~3.5 MB
**Format:** CSV
**Generated:** 2025
**Random Seed:** 42 (reproducible)

---

## Feature Categories

### 1. Customer Demographics (5 features)

#### `customer_id` (string)
- **Description:** Unique customer identifier
- **Format:** CUST000001 to CUST020000
- **Missing Data:** None
- **Usage:** Primary key for customer identification

#### `age` (integer)
- **Description:** Customer age in years
- **Range:** 18-75 years
- **Distribution:** Normal (mean=38, sd=12)
- **Missing Data:** None
- **Usage:** Demographic segmentation, stratification variable

#### `gender` (categorical)
- **Description:** Customer gender identity
- **Categories:** Male (48%), Female (49%), Non-binary (3%)
- **Missing Data:** None
- **Usage:** Stratification, balance checking

#### `location` (categorical)
- **Description:** Customer location type
- **Categories:**
  - Urban (45%)
  - Suburban (40%)
  - Rural (15%)
- **Missing Data:** None
- **Usage:** Geographic segmentation, blocking variable

#### `income_level` (categorical)
- **Description:** Household income bracket
- **Categories:**
  - Low (11%)
  - Medium (51%)
  - High (31%)
  - Very High (7%)
- **Missing Data:** None
- **Correlations:** Positively correlated with age (up to age 50)
- **Usage:** Stratification, treatment effect moderator

---

### 2. Shopping Behavior (5 features)

#### `account_age_days` (integer)
- **Description:** Days since customer registration
- **Range:** 0-3,650 days (0-10 years)
- **Distribution:** Exponential (scale varies by age)
- **Missing Data:** None
- **Correlations:** Increases with customer age
- **Usage:** Covariate for adjustment, historical activity indicator

#### `total_orders` (integer)
- **Description:** Total number of orders placed
- **Range:** 0-200 orders
- **Distribution:** Poisson (lambda varies by income and account age)
- **Missing Data:** None
- **Correlations:**
  - Positive with account_age_days
  - Positive with income_level
  - Strong positive with lifetime_value (r=0.80)
- **Usage:** Key engagement metric, propensity score variable

#### `avg_order_value` (float)
- **Description:** Average monetary value per order (USD)
- **Range:** $10-$450
- **Distribution:** Normal (mean varies by income level)
  - Low income: ~$30
  - Medium income: ~$60
  - High income: ~$120
  - Very High income: ~$200
- **Missing Data:** None
- **Correlations:** Strong positive with income_level
- **Usage:** Customer value metric, outcome variable

#### `last_order_days_ago` (integer)
- **Description:** Days since last purchase
- **Range:** 0-365 days
- **Distribution:** Exponential (scale=60)
- **Missing Data:** None
- **Correlations:** Positive with churn_probability
- **Usage:** Recency metric, churn predictor

#### `product_category_preference` (categorical)
- **Description:** Primary product category purchased
- **Categories:** Electronics, Fashion, Home, Books, Sports
- **Distribution:** Varies by age and gender
  - Younger (<30): Electronics, Fashion preferred
  - Middle-aged (30-50): Home, Fashion preferred
  - Older (>50): Books, Home preferred
- **Missing Data:** None
- **Usage:** Segmentation variable, personalization basis

---

### 3. Engagement Metrics (5 features)

#### `email_open_rate` (float)
- **Description:** Percentage of marketing emails opened
- **Range:** 0-100%
- **Distribution:** Beta distribution (higher for active customers)
- **Missing Data:** 5%
- **Correlations:** Positive with total_orders, conversion_rate
- **Usage:** Engagement indicator, marketing response predictor

#### `website_visits_per_month` (integer)
- **Description:** Average monthly website visits
- **Range:** 0-50 visits
- **Distribution:** Poisson (higher for younger, urban customers)
- **Missing Data:** None
- **Correlations:** Negative with age, positive with urban location
- **Usage:** Engagement metric, digital behavior indicator

#### `mobile_app_user` (binary categorical)
- **Description:** Whether customer uses mobile app
- **Categories:** Yes, No
- **Distribution:** More likely for younger customers
- **Missing Data:** None
- **Correlations:** Negative with age
- **Usage:** Channel preference indicator

#### `loyalty_program_member` (binary categorical)
- **Description:** Whether customer enrolled in loyalty program
- **Categories:** Yes, No
- **Distribution:** More likely for frequent shoppers
- **Missing Data:** None
- **Correlations:** Positive with total_orders
- **Usage:** Loyalty indicator, treatment effect moderator

#### `customer_service_interactions` (integer)
- **Description:** Number of customer service contacts
- **Range:** 0-20 interactions
- **Distribution:** Poisson (proportional to order count)
- **Missing Data:** 5%
- **Usage:** Service quality indicator, satisfaction proxy

---

### 4. Behavioral Indicators (4 features)

#### `cart_abandonment_rate` (float)
- **Description:** Percentage of shopping carts abandoned
- **Range:** 0-100%
- **Distribution:** Inversely related to engagement
- **Missing Data:** 5%
- **Correlations:** Negative with email_open_rate
- **Usage:** Conversion barrier indicator, intervention target

#### `review_count` (integer)
- **Description:** Number of product reviews written
- **Range:** 0-100 reviews
- **Distribution:** Binomial (15% of orders reviewed)
- **Missing Data:** 5%
- **Correlations:** Proportional to total_orders
- **Usage:** Engagement depth indicator

#### `avg_rating_given` (float)
- **Description:** Average star rating given in reviews
- **Range:** 1.0-5.0 stars
- **Distribution:** Beta distribution (skewed toward 4-5 stars)
- **Missing Data:** 5%
- **Usage:** Satisfaction indicator, sentiment proxy

#### `social_media_follower` (binary categorical)
- **Description:** Whether customer follows brand on social media
- **Categories:** Yes, No
- **Distribution:** More likely for engaged customers
- **Missing Data:** None
- **Correlations:** Positive with email_open_rate
- **Usage:** Brand affinity indicator

---

### 5. Target Variables (4 features)

#### `conversion_rate` (float)
- **Description:** Predicted conversion probability (%)
- **Range:** 0-100%
- **Distribution:** Complex function of multiple factors
- **Key Drivers:**
  - Age (peaks at 40)
  - Income level
  - Engagement metrics
  - Loyalty program membership
- **Missing Data:** None
- **Usage:** Primary outcome for marketing experiments

#### `lifetime_value` (float)
- **Description:** Predicted customer lifetime value (USD)
- **Range:** $0-$10,000
- **Calculation:** total_orders × avg_order_value × engagement_multiplier
- **Missing Data:** None
- **Correlations:** Very strong with total_orders (r=0.80)
- **Usage:** Business outcome metric, customer segmentation

#### `churn_probability` (float)
- **Description:** Predicted probability of customer churn (%)
- **Range:** 0-100%
- **Key Drivers:**
  - Recency (days since last order)
  - Low engagement metrics
  - High cart abandonment
- **Missing Data:** None
- **Correlations:** Positive with last_order_days_ago (r=0.62)
- **Usage:** Retention experiment outcome

#### `response_to_marketing` (binary integer)
- **Description:** Binary indicator of marketing campaign response
- **Categories:** 0 (no response), 1 (responded)
- **Distribution:** ~41% response rate
- **Key Predictors:**
  - Email open rate
  - Total orders
  - Recency
- **Missing Data:** None
- **Usage:** Binary outcome for treatment effect estimation

---

## Data Generation Process

### Correlations Built Into Data

1. **Age → Income Level**
   - Income increases with age up to ~50 years
   - Simulates career progression

2. **Income Level → Order Value**
   - Higher income customers spend more per order
   - Strong positive correlation

3. **Age → Account Age**
   - Older customers have older accounts
   - Realistic tenure patterns

4. **Total Orders → Lifetime Value**
   - Strong positive correlation (r=0.80)
   - Mathematical relationship: LTV = orders × value × engagement

5. **Engagement → Conversion**
   - Email open rate, loyalty, recency all predict conversion
   - Multi-factor influence

6. **Recency → Churn**
   - Recent purchases reduce churn risk
   - Exponential relationship

7. **Age → Mobile App Usage**
   - Younger customers more likely to use app
   - Digital divide effect

### Missing Data Patterns

- **Mechanism:** Missing Completely At Random (MCAR)
- **Rate:** 5% per eligible column
- **Affected Columns:**
  - email_open_rate
  - customer_service_interactions
  - cart_abandonment_rate
  - review_count
  - avg_rating_given
- **Protected Columns:** All demographic and target variables are complete

---

## Statistical Properties

### Validation Results

✓ **Structure:** 20,000 rows × 24 columns
✓ **Completeness:** 98.97%
✓ **Duplicates:** None
✓ **Correlations:** As expected (see above)
✓ **Distributions:** Realistic ranges maintained
✓ **Consistency:** Logical relationships preserved

### Key Statistics

- **Average Customer Age:** 37.8 years
- **Average Total Orders:** 7.4 orders
- **Average Order Value:** $85.92
- **Average Lifetime Value:** $810.42
- **Marketing Response Rate:** 41.0%
- **Average Conversion Rate:** 44.5%
- **Average Churn Probability:** 46.3%

---

## Usage Guidelines

### For Sampling Demonstrations

**Stratification Variables:**
- `age` (create age groups: 18-30, 31-45, 46-60, 61-75)
- `gender`
- `location`
- `income_level`

**Sample Size Recommendations:**
- Simple random sampling: n=500-2,000
- Stratified sampling: n=100-500 per stratum
- Cluster sampling: 5-20 clusters

### For Experimental Design

**Treatment Assignment Variables:**
- Use `customer_id` for randomization
- Block on `location`, `income_level`, or `loyalty_program_member`
- Stratify by `age_group` or `gender`

**Balance Check Variables:**
Priority variables for checking treatment-control balance:
1. `age` (continuous)
2. `gender` (categorical)
3. `income_level` (categorical)
4. `total_orders` (continuous)
5. `avg_order_value` (continuous)
6. `last_order_days_ago` (continuous)

**Outcome Variables:**
- **Binary outcomes:** `response_to_marketing`
- **Continuous outcomes:** `conversion_rate`, `lifetime_value`, `avg_order_value`
- **Time-to-event:** Days until next purchase (can be derived)

### For Propensity Score Analysis

**Covariates for Propensity Model:**
Include in logistic regression to predict treatment assignment:
- Age
- Gender
- Location
- Income level
- Total orders
- Account age days
- Email open rate
- Loyalty program member

---

## Common Analysis Scenarios

### Scenario 1: Marketing Campaign Effectiveness
**Treatment:** New email campaign vs. standard campaign
**Outcome:** `response_to_marketing`
**Covariates:** `email_open_rate`, `age`, `income_level`
**Design:** Stratified randomization by `income_level`

### Scenario 2: Website Redesign Impact
**Treatment:** New design vs. old design
**Outcome:** `conversion_rate`, `cart_abandonment_rate`
**Covariates:** `age`, `mobile_app_user`, `website_visits_per_month`
**Design:** Randomized block design, block by `location`

### Scenario 3: Loyalty Program Value
**Treatment:** Enrolling non-members vs. control
**Outcome:** `lifetime_value`, `churn_probability`
**Covariates:** `total_orders`, `account_age_days`, `avg_order_value`
**Design:** Propensity score matching

### Scenario 4: Pricing Experiment
**Treatment:** Three price points (factorial design)
**Outcome:** `avg_order_value`, `total_orders`
**Covariates:** `income_level`, `product_category_preference`
**Design:** 3-level factorial, stratify by income

---

## Data Access

### Loading the Data

**Python (pandas):**
```python
import pandas as pd

df = pd.read_csv('data/raw/ecommerce_data.csv')
print(df.shape)
print(df.head())
```

**R:**
```r
df <- read.csv('data/raw/ecommerce_data.csv')
dim(df)
head(df)
```

### Handling Missing Data

**Options:**
1. **Complete case analysis:** Drop rows with any missing values
   ```python
   df_complete = df.dropna()
   ```

2. **Mean/median imputation:** For numerical features
   ```python
   df['email_open_rate'].fillna(df['email_open_rate'].median(), inplace=True)
   ```

3. **Mode imputation:** For categorical features (not needed here)

4. **Multiple imputation:** For sophisticated analysis
   ```python
   from sklearn.experimental import enable_iterative_imputer
   from sklearn.impute import IterativeImputer

   imputer = IterativeImputer(random_state=42)
   df_imputed = pd.DataFrame(
       imputer.fit_transform(df.select_dtypes(include=[np.number])),
       columns=df.select_dtypes(include=[np.number]).columns
   )
   ```

---

## Version History

**v1.0** (2025-01-15)
- Initial dataset generation
- 20,000 customers
- 24 features
- Validated correlations and distributions

---

## Contact & Support

For questions about this dataset or to report issues:
- **Repository:** GitHub DOE_Simulator
- **Documentation:** See README.md
- **Issues:** Use GitHub issue tracker

---

## Citation

If using this dataset for educational purposes, please cite:

```
DOE Simulator Team (2025). E-commerce Customer Dataset for Design of Experiments.
DOE Simulator Project. https://github.com/[your-repo]/DOE_Simulator
```

---

**Last Updated:** 2025-01-15
**Dataset Version:** 1.0
**Documentation Version:** 1.0
