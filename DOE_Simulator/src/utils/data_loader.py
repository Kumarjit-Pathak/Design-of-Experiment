"""
Data Loader Module

This module provides functions to load and validate datasets for DOE experiments.
It handles CSV files, performs basic validation, and provides utilities for
data preprocessing.

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
import warnings


class DataLoadError(Exception):
    """Custom exception for data loading errors."""
    pass


def load_data(
    file_path: str,
    required_columns: Optional[List[str]] = None,
    dtype_dict: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Load data from CSV file with validation.

    Args:
        file_path: Path to CSV file
        required_columns: List of columns that must be present
        dtype_dict: Dictionary mapping column names to data types

    Returns:
        pandas DataFrame with loaded data

    Raises:
        DataLoadError: If file cannot be loaded or validation fails

    Example:
        >>> df = load_data(
        ...     'data/raw/ecommerce_data.csv',
        ...     required_columns=['customer_id', 'age', 'gender']
        ... )
    """
    try:
        df = pd.read_csv(file_path, dtype=dtype_dict)
    except FileNotFoundError:
        raise DataLoadError(f"File not found: {file_path}")
    except pd.errors.EmptyDataError:
        raise DataLoadError(f"File is empty: {file_path}")
    except Exception as e:
        raise DataLoadError(f"Error loading file: {str(e)}")

    # Validate required columns
    if required_columns:
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise DataLoadError(
                f"Required columns missing from dataset: {missing_columns}"
            )

    print(f"[OK] Data loaded: {len(df):,} rows x {len(df.columns)} columns")

    return df


def validate_data_quality(
    df: pd.DataFrame,
    check_duplicates: bool = True,
    check_missing: bool = True,
    max_missing_pct: float = 20.0
) -> Dict[str, Any]:
    """
    Perform data quality checks.

    Args:
        df: DataFrame to validate
        check_duplicates: Whether to check for duplicate rows
        check_missing: Whether to check for missing data
        max_missing_pct: Maximum acceptable percentage of missing data

    Returns:
        Dictionary with validation results

    Example:
        >>> quality = validate_data_quality(df)
        >>> print(f"Duplicates: {quality['duplicates']}")
    """
    results = {}

    # Check for duplicate rows
    if check_duplicates:
        duplicates = df.duplicated().sum()
        results['duplicates'] = duplicates
        if duplicates > 0:
            warnings.warn(f"Found {duplicates} duplicate rows", UserWarning)

    # Check for missing data
    if check_missing:
        missing_counts = df.isnull().sum()
        missing_pct = (missing_counts / len(df)) * 100

        results['missing_counts'] = missing_counts[missing_counts > 0].to_dict()
        results['missing_pct'] = missing_pct[missing_pct > 0].to_dict()

        # Warn about columns with high missingness
        high_missing = missing_pct[missing_pct > max_missing_pct]
        if not high_missing.empty:
            warnings.warn(
                f"Columns with >{max_missing_pct}% missing data: "
                f"{high_missing.to_dict()}",
                UserWarning
            )

    # Data shape
    results['n_rows'] = len(df)
    results['n_cols'] = len(df.columns)

    # Memory usage
    results['memory_mb'] = df.memory_usage(deep=True).sum() / (1024**2)

    return results


def get_column_info(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get detailed information about DataFrame columns.

    Args:
        df: DataFrame to analyze

    Returns:
        DataFrame with column information

    Example:
        >>> info = get_column_info(df)
        >>> print(info)
    """
    info = pd.DataFrame({
        'dtype': df.dtypes,
        'non_null_count': df.count(),
        'null_count': df.isnull().sum(),
        'null_pct': (df.isnull().sum() / len(df) * 100).round(2),
        'unique_count': df.nunique(),
        'sample_values': [df[col].dropna().head(3).tolist() for col in df.columns]
    })

    return info


def identify_column_types(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Identify and categorize column types.

    Args:
        df: DataFrame to analyze

    Returns:
        Dictionary mapping column types to column names

    Example:
        >>> types = identify_column_types(df)
        >>> print(f"Numerical columns: {types['numerical']}")
    """
    types = {
        'numerical': [],
        'categorical': [],
        'binary': [],
        'datetime': [],
        'text': []
    }

    for col in df.columns:
        # Datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            types['datetime'].append(col)

        # Numerical
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Check if binary (only 0 and 1)
            unique_vals = df[col].dropna().unique()
            if set(unique_vals).issubset({0, 1}):
                types['binary'].append(col)
            else:
                types['numerical'].append(col)

        # Categorical or Text
        elif pd.api.types.is_object_dtype(df[col]):
            unique_count = df[col].nunique()
            # If few unique values, likely categorical
            if unique_count < 20:
                # Check if binary (Yes/No, True/False, etc.)
                unique_vals = df[col].dropna().unique()
                if len(unique_vals) == 2:
                    types['binary'].append(col)
                else:
                    types['categorical'].append(col)
            else:
                types['text'].append(col)

    return types


def handle_missing_data(
    df: pd.DataFrame,
    strategy: str = 'drop',
    columns: Optional[List[str]] = None,
    fill_value: Any = None
) -> pd.DataFrame:
    """
    Handle missing data in DataFrame.

    Args:
        df: DataFrame with missing data
        strategy: Strategy for handling missing data
                  Options: 'drop', 'fill_mean', 'fill_median', 'fill_mode', 'fill_value'
        columns: List of columns to apply strategy to (None = all columns)
        fill_value: Value to use when strategy='fill_value'

    Returns:
        DataFrame with missing data handled

    Example:
        >>> df_clean = handle_missing_data(df, strategy='fill_median',
        ...                                 columns=['age', 'income'])
    """
    df_copy = df.copy()

    if columns is None:
        columns = df_copy.columns.tolist()

    if strategy == 'drop':
        df_copy = df_copy.dropna(subset=columns)

    elif strategy == 'fill_mean':
        for col in columns:
            if pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col].fillna(df_copy[col].mean(), inplace=True)

    elif strategy == 'fill_median':
        for col in columns:
            if pd.api.types.is_numeric_dtype(df_copy[col]):
                df_copy[col].fillna(df_copy[col].median(), inplace=True)

    elif strategy == 'fill_mode':
        for col in columns:
            mode_value = df_copy[col].mode()[0] if not df_copy[col].mode().empty else None
            if mode_value is not None:
                df_copy[col].fillna(mode_value, inplace=True)

    elif strategy == 'fill_value':
        if fill_value is None:
            raise ValueError("fill_value must be specified when strategy='fill_value'")
        for col in columns:
            df_copy[col].fillna(fill_value, inplace=True)

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    print(f"[OK] Missing data handled using strategy: {strategy}")

    return df_copy


def create_age_groups(
    df: pd.DataFrame,
    age_column: str = 'age',
    bins: Optional[List[int]] = None,
    labels: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Create age group categories from continuous age variable.

    Args:
        df: DataFrame containing age column
        age_column: Name of age column
        bins: List of bin edges (default: [18, 30, 45, 60, 75])
        labels: List of category labels

    Returns:
        DataFrame with added age_group column

    Example:
        >>> df = create_age_groups(df, age_column='age')
        >>> print(df['age_group'].value_counts())
    """
    df_copy = df.copy()

    if bins is None:
        bins = [0, 30, 45, 60, 100]

    if labels is None:
        labels = [f"{bins[i]}-{bins[i+1]}" for i in range(len(bins)-1)]

    df_copy['age_group'] = pd.cut(
        df_copy[age_column],
        bins=bins,
        labels=labels,
        include_lowest=True
    )

    print(f"[OK] Age groups created: {df_copy['age_group'].value_counts().to_dict()}")

    return df_copy


def filter_data(
    df: pd.DataFrame,
    filters: Dict[str, Any]
) -> pd.DataFrame:
    """
    Filter DataFrame based on conditions.

    Args:
        df: DataFrame to filter
        filters: Dictionary of column: value pairs or column: (min, max) for ranges

    Returns:
        Filtered DataFrame

    Example:
        >>> filtered = filter_data(df, {
        ...     'gender': 'Female',
        ...     'age': (25, 45),
        ...     'location': ['Urban', 'Suburban']
        ... })
    """
    df_filtered = df.copy()

    for column, condition in filters.items():
        if column not in df_filtered.columns:
            warnings.warn(f"Column '{column}' not found in DataFrame", UserWarning)
            continue

        # Range filter (tuple with min, max)
        if isinstance(condition, tuple) and len(condition) == 2:
            min_val, max_val = condition
            df_filtered = df_filtered[
                (df_filtered[column] >= min_val) & (df_filtered[column] <= max_val)
            ]

        # List filter (multiple values)
        elif isinstance(condition, list):
            df_filtered = df_filtered[df_filtered[column].isin(condition)]

        # Exact match
        else:
            df_filtered = df_filtered[df_filtered[column] == condition]

    print(f"[OK] Filtered data: {len(df_filtered):,} rows remaining")

    return df_filtered


def save_data(
    df: pd.DataFrame,
    output_path: str,
    index: bool = False
) -> None:
    """
    Save DataFrame to CSV file.

    Args:
        df: DataFrame to save
        output_path: Path for output CSV file
        index: Whether to include index in output

    Example:
        >>> save_data(df, 'data/processed/sampled_data.csv')
    """
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df.to_csv(output_path, index=index)
    print(f"[SAVED] Data saved to: {output_path}")


def print_data_summary(df: pd.DataFrame) -> None:
    """
    Print comprehensive data summary.

    Args:
        df: DataFrame to summarize
    """
    print("\n" + "="*70)
    print("DATA SUMMARY")
    print("="*70)

    print(f"\nShape: {df.shape[0]:,} rows x {df.shape[1]} columns")

    # Missing data
    missing = df.isnull().sum()
    if missing.sum() > 0:
        print(f"\nMissing Data:")
        for col, count in missing[missing > 0].items():
            print(f"  {col}: {count} ({count/len(df)*100:.1f}%)")
    else:
        print("\nMissing Data: None")

    # Column types
    types = identify_column_types(df)
    print(f"\nColumn Types:")
    for type_name, cols in types.items():
        if cols:
            print(f"  {type_name}: {len(cols)} columns")

    # Numerical summary
    numerical_cols = df.select_dtypes(include=[np.number]).columns
    if len(numerical_cols) > 0:
        print(f"\nNumerical Features Summary:")
        print(df[numerical_cols].describe().round(2).to_string())

    print("\n" + "="*70 + "\n")


# Example usage
if __name__ == "__main__":
    # Example: Load and analyze data
    print("Loading e-commerce data...")

    try:
        df = load_data(
            'data/raw/ecommerce_data.csv',
            required_columns=['customer_id', 'age', 'gender']
        )

        print_data_summary(df)

        # Check data quality
        quality = validate_data_quality(df)
        print(f"Data quality checks:")
        print(f"  Duplicates: {quality['duplicates']}")
        print(f"  Memory usage: {quality['memory_mb']:.2f} MB")

        # Identify column types
        types = identify_column_types(df)
        print(f"\nColumn types identified:")
        for type_name, cols in types.items():
            if cols:
                print(f"  {type_name}: {cols[:5]}...")  # Show first 5

    except DataLoadError as e:
        print(f"[ERROR] {e}")
