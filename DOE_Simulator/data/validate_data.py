"""
Data Validation Script

This script validates the generated e-commerce dataset to ensure:
- Correct number of rows and columns
- No duplicate customer IDs
- Realistic feature distributions
- Expected correlations between features
- Appropriate missing data patterns

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns


def validate_basic_structure(df):
    """Validate basic dataset structure."""
    print("\n" + "="*70)
    print("BASIC STRUCTURE VALIDATION")
    print("="*70)

    # Check dimensions
    expected_rows = 20000
    expected_cols = 24

    print(f"\n[CHECK] Number of rows: {len(df):,}")
    if len(df) == expected_rows:
        print("  [PASS] Correct number of rows")
    else:
        print(f"  [FAIL] Expected {expected_rows:,} rows, got {len(df):,}")

    print(f"\n[CHECK] Number of columns: {len(df.columns)}")
    if len(df.columns) == expected_cols:
        print("  [PASS] Correct number of columns")
    else:
        print(f"  [FAIL] Expected {expected_cols} columns, got {len(df.columns)}")

    # Check for duplicate IDs
    print(f"\n[CHECK] Duplicate customer IDs")
    duplicates = df['customer_id'].duplicated().sum()
    if duplicates == 0:
        print("  [PASS] No duplicate customer IDs")
    else:
        print(f"  [FAIL] Found {duplicates} duplicate IDs")

    # Check data types
    print(f"\n[CHECK] Data types:")
    print(df.dtypes.value_counts().to_string())


def validate_distributions(df):
    """Validate feature distributions."""
    print("\n" + "="*70)
    print("DISTRIBUTION VALIDATION")
    print("="*70)

    # Age distribution
    print(f"\n[CHECK] Age distribution:")
    print(f"  Min: {df['age'].min()}, Max: {df['age'].max()}")
    print(f"  Mean: {df['age'].mean():.1f}, Median: {df['age'].median():.1f}")
    if 18 <= df['age'].min() and df['age'].max() <= 75:
        print("  [PASS] Age within expected range (18-75)")
    else:
        print("  [FAIL] Age outside expected range")

    # Income level distribution
    print(f"\n[CHECK] Income level distribution:")
    print(df['income_level'].value_counts(normalize=True).mul(100).round(1).to_string())

    # Gender distribution
    print(f"\n[CHECK] Gender distribution:")
    print(df['gender'].value_counts(normalize=True).mul(100).round(1).to_string())

    # Location distribution
    print(f"\n[CHECK] Location distribution:")
    print(df['location'].value_counts(normalize=True).mul(100).round(1).to_string())

    # Order value
    print(f"\n[CHECK] Average order value:")
    print(f"  Min: ${df['avg_order_value'].min():.2f}, Max: ${df['avg_order_value'].max():.2f}")
    print(f"  Mean: ${df['avg_order_value'].mean():.2f}")

    # Lifetime value
    print(f"\n[CHECK] Lifetime value:")
    print(f"  Min: ${df['lifetime_value'].min():.2f}, Max: ${df['lifetime_value'].max():.2f}")
    print(f"  Mean: ${df['lifetime_value'].mean():.2f}")


def validate_correlations(df):
    """Validate expected correlations between features."""
    print("\n" + "="*70)
    print("CORRELATION VALIDATION")
    print("="*70)

    # Age vs Total Orders (should be positive)
    corr_age_orders = df[['age', 'total_orders']].corr().iloc[0, 1]
    print(f"\n[CHECK] Age vs Total Orders correlation: {corr_age_orders:.3f}")
    if corr_age_orders > 0:
        print("  [PASS] Positive correlation as expected")
    else:
        print("  [WARN] Expected positive correlation")

    # Total Orders vs Lifetime Value (should be strongly positive)
    corr_orders_ltv = df[['total_orders', 'lifetime_value']].corr().iloc[0, 1]
    print(f"\n[CHECK] Total Orders vs Lifetime Value correlation: {corr_orders_ltv:.3f}")
    if corr_orders_ltv > 0.7:
        print("  [PASS] Strong positive correlation as expected")
    else:
        print("  [WARN] Expected strong positive correlation (>0.7)")

    # Email Open Rate vs Conversion Rate (should be positive)
    corr_email_conversion = df[['email_open_rate', 'conversion_rate']].corr().iloc[0, 1]
    print(f"\n[CHECK] Email Open Rate vs Conversion Rate: {corr_email_conversion:.3f}")
    if corr_email_conversion > 0:
        print("  [PASS] Positive correlation as expected")
    else:
        print("  [WARN] Expected positive correlation")

    # Last Order Days Ago vs Churn Probability (should be positive)
    corr_recency_churn = df[['last_order_days_ago', 'churn_probability']].corr().iloc[0, 1]
    print(f"\n[CHECK] Recency vs Churn Probability: {corr_recency_churn:.3f}")
    if corr_recency_churn > 0:
        print("  [PASS] Positive correlation as expected")
    else:
        print("  [WARN] Expected positive correlation")


def validate_missing_data(df):
    """Validate missing data patterns."""
    print("\n" + "="*70)
    print("MISSING DATA VALIDATION")
    print("="*70)

    missing_counts = df.isnull().sum()
    missing_cols = missing_counts[missing_counts > 0]

    print(f"\n[CHECK] Columns with missing data: {len(missing_cols)}")
    print(f"\n[CHECK] Missing data percentages:")
    for col, count in missing_cols.items():
        pct = count / len(df) * 100
        print(f"  {col}: {count} ({pct:.1f}%)")
        if 4 <= pct <= 6:
            print(f"    [PASS] Within expected range (4-6%)")
        else:
            print(f"    [WARN] Outside expected range")

    # Check that critical columns have no missing data
    critical_cols = ['customer_id', 'age', 'gender', 'income_level',
                     'total_orders', 'response_to_marketing']
    print(f"\n[CHECK] Critical columns completeness:")
    all_complete = True
    for col in critical_cols:
        missing = df[col].isnull().sum()
        if missing == 0:
            print(f"  {col}: [PASS] Complete")
        else:
            print(f"  {col}: [FAIL] {missing} missing values")
            all_complete = False

    if all_complete:
        print("\n  [PASS] All critical columns are complete")


def validate_logical_consistency(df):
    """Validate logical consistency of data."""
    print("\n" + "="*70)
    print("LOGICAL CONSISTENCY VALIDATION")
    print("="*70)

    # Account age should not exceed realistic limits
    print(f"\n[CHECK] Account age consistency:")
    max_account_age = df['account_age_days'].max()
    print(f"  Maximum account age: {max_account_age} days ({max_account_age/365:.1f} years)")
    if max_account_age <= 3650:
        print("  [PASS] Within realistic range (<=10 years)")
    else:
        print("  [FAIL] Exceeds realistic range")

    # Total orders should be reasonable given account age
    print(f"\n[CHECK] Orders vs Account Age consistency:")
    df_temp = df[df['account_age_days'] > 0].copy()
    df_temp['orders_per_year'] = (df_temp['total_orders'] / df_temp['account_age_days']) * 365
    avg_orders_per_year = df_temp['orders_per_year'].mean()
    print(f"  Average orders per year: {avg_orders_per_year:.1f}")
    if avg_orders_per_year <= 100:
        print("  [PASS] Reasonable order frequency")
    else:
        print("  [WARN] Very high order frequency")

    # Conversion rate should be between 0 and 100
    print(f"\n[CHECK] Conversion rate range:")
    if df['conversion_rate'].min() >= 0 and df['conversion_rate'].max() <= 100:
        print("  [PASS] Conversion rate within valid range (0-100%)")
    else:
        print("  [FAIL] Conversion rate outside valid range")

    # Response to marketing should be binary
    print(f"\n[CHECK] Marketing response is binary:")
    unique_responses = df['response_to_marketing'].unique()
    if set(unique_responses) == {0, 1}:
        print("  [PASS] Binary values (0, 1)")
    else:
        print(f"  [FAIL] Found values: {unique_responses}")


def validate_categorical_features(df):
    """Validate categorical features."""
    print("\n" + "="*70)
    print("CATEGORICAL FEATURES VALIDATION")
    print("="*70)

    categorical_cols = {
        'gender': ['Male', 'Female', 'Non-binary'],
        'location': ['Urban', 'Suburban', 'Rural'],
        'income_level': ['Low', 'Medium', 'High', 'Very High'],
        'education': ['High School', 'Bachelor', 'Master', 'PhD'],
        'product_category_preference': ['Electronics', 'Fashion', 'Home', 'Books', 'Sports'],
        'mobile_app_user': ['Yes', 'No'],
        'loyalty_program_member': ['Yes', 'No'],
        'social_media_follower': ['Yes', 'No']
    }

    for col, expected_values in categorical_cols.items():
        print(f"\n[CHECK] {col}:")
        actual_values = set(df[col].unique())
        expected_set = set(expected_values)

        if actual_values == expected_set:
            print(f"  [PASS] All expected categories present")
        else:
            missing = expected_set - actual_values
            extra = actual_values - expected_set
            if missing:
                print(f"  [WARN] Missing categories: {missing}")
            if extra:
                print(f"  [WARN] Unexpected categories: {extra}")


def generate_summary_report(df):
    """Generate summary validation report."""
    print("\n" + "="*70)
    print("VALIDATION SUMMARY")
    print("="*70)

    print(f"\nDataset Shape: {df.shape[0]:,} rows x {df.shape[1]} columns")
    print(f"Memory Usage: {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    print(f"\nData Quality Metrics:")
    print(f"  - Total cells: {df.shape[0] * df.shape[1]:,}")
    print(f"  - Missing cells: {df.isnull().sum().sum():,}")
    print(f"  - Completeness: {(1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100:.2f}%")

    print(f"\nNumerical Features Summary:")
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    print(f"  - Count: {len(numerical_cols)}")
    print(f"  - Mean of means: {df[numerical_cols].mean().mean():.2f}")
    print(f"  - Mean of std devs: {df[numerical_cols].std().mean():.2f}")

    print(f"\nCategorical Features Summary:")
    categorical_cols = df.select_dtypes(include=['object']).columns
    print(f"  - Count: {len(categorical_cols)}")
    print(f"  - Average cardinality: {df[categorical_cols].nunique().mean():.1f}")

    print(f"\n[SUCCESS] Data validation complete!")
    print(f"[INFO] Dataset is ready for DOE simulations")


def main():
    """Main validation function."""
    print("\n" + "="*70)
    print("E-COMMERCE DATASET VALIDATION")
    print("="*70)

    # Load data
    data_path = 'data/raw/ecommerce_data.csv'
    print(f"\nLoading data from: {data_path}")

    try:
        df = pd.read_csv(data_path)
        print(f"[OK] Data loaded successfully")
    except FileNotFoundError:
        print(f"[ERROR] File not found: {data_path}")
        return
    except Exception as e:
        print(f"[ERROR] Failed to load data: {str(e)}")
        return

    # Run validation checks
    validate_basic_structure(df)
    validate_distributions(df)
    validate_correlations(df)
    validate_missing_data(df)
    validate_logical_consistency(df)
    validate_categorical_features(df)
    generate_summary_report(df)

    print("\n" + "="*70)
    print("[SUCCESS] All validation checks complete!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
