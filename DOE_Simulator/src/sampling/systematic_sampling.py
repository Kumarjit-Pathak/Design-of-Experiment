"""
Systematic Sampling Module

This module implements systematic sampling where every kth element is selected
after a random start. This method is simple to implement and provides good
coverage, but can be biased if there's periodicity in the data.

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import sys
import os
import warnings

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import load_config, validate_config
from utils.data_loader import load_data, save_data, print_data_summary


def systematic_sample(
    df: pd.DataFrame,
    sample_size: int,
    random_start: Optional[int] = None,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform systematic sampling.

    The sampling interval k is calculated as k = N / n (population size / sample size).
    Starting from a random point between 1 and k, every kth element is selected.

    Args:
        df: DataFrame to sample from
        sample_size: Desired sample size
        random_start: Starting index (if None, randomly selected)
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame containing systematic sample

    Example:
        >>> sample = systematic_sample(df, sample_size=1000, random_seed=42)
    """
    # Set random seed
    if random_seed is not None:
        np.random.seed(random_seed)

    population_size = len(df)

    # Validate sample size
    if sample_size > population_size:
        warnings.warn(
            f"Sample size ({sample_size}) exceeds population size ({population_size}). "
            f"Using full dataset.",
            UserWarning
        )
        return df.copy()

    # Calculate sampling interval
    k = population_size / sample_size

    print(f"[INFO] Population size: {population_size:,}")
    print(f"[INFO] Sample size: {sample_size:,}")
    print(f"[INFO] Sampling interval (k): {k:.2f}")

    # Determine random start
    if random_start is None:
        random_start = np.random.randint(0, int(np.ceil(k)))

    print(f"[INFO] Random start index: {random_start}")

    # Generate sample indices using systematic sampling
    indices = []
    current_index = random_start

    while len(indices) < sample_size and current_index < population_size:
        indices.append(current_index)
        current_index += int(np.round(k))

    # Handle edge case: if we didn't get enough samples due to rounding
    if len(indices) < sample_size:
        # Add remaining indices from the end
        remaining = sample_size - len(indices)
        additional_indices = list(range(population_size - remaining, population_size))
        # Remove duplicates
        additional_indices = [idx for idx in additional_indices if idx not in indices]
        indices.extend(additional_indices[:remaining])

    # Extract sample
    sample = df.iloc[indices].reset_index(drop=True)

    print(f"[OK] Systematic sample generated: {len(sample):,} observations")

    return sample


def detect_periodicity(
    df: pd.DataFrame,
    column: str,
    max_period: int = 50
) -> Dict[str, Any]:
    """
    Detect potential periodicity in a column using autocorrelation.

    Periodicity in data can bias systematic sampling. This function helps
    identify if the data has periodic patterns.

    Args:
        df: DataFrame to analyze
        column: Column name to check for periodicity
        max_period: Maximum period to check (default: 50)

    Returns:
        Dictionary with periodicity detection results

    Example:
        >>> results = detect_periodicity(df, 'sales', max_period=30)
        >>> if results['periodic']:
        ...     print(f"Warning: Period detected at lag {results['period']}")
    """
    if column not in df.columns:
        raise ValueError(f"Column '{column}' not found in DataFrame")

    if not pd.api.types.is_numeric_dtype(df[column]):
        warnings.warn(f"Column '{column}' is not numerical, skipping periodicity check")
        return {'periodic': False, 'period': None, 'max_correlation': 0}

    # Remove NaN values
    data = df[column].dropna().values

    if len(data) < max_period * 2:
        warnings.warn("Insufficient data for reliable periodicity detection")
        return {'periodic': False, 'period': None, 'max_correlation': 0}

    # Calculate autocorrelations
    autocorrs = []
    for lag in range(1, min(max_period, len(data) // 2)):
        # Simple autocorrelation calculation
        data_lagged = data[:-lag]
        data_current = data[lag:]

        if len(data_lagged) > 0:
            corr = np.corrcoef(data_lagged, data_current)[0, 1]
            autocorrs.append((lag, corr))

    if not autocorrs:
        return {'periodic': False, 'period': None, 'max_correlation': 0}

    # Find maximum correlation (excluding lag 0)
    max_lag, max_corr = max(autocorrs, key=lambda x: abs(x[1]))

    # Consider periodic if correlation > 0.5
    is_periodic = abs(max_corr) > 0.5

    results = {
        'periodic': is_periodic,
        'period': max_lag if is_periodic else None,
        'max_correlation': max_corr,
        'all_correlations': autocorrs
    }

    return results


def assess_systematic_coverage(
    population_size: int,
    sample_size: int,
    k: float
) -> Dict[str, Any]:
    """
    Assess how well systematic sampling covers the population.

    Args:
        population_size: Size of population
        sample_size: Size of sample
        k: Sampling interval

    Returns:
        Dictionary with coverage metrics

    Example:
        >>> coverage = assess_systematic_coverage(20000, 1000, 20.0)
    """
    # Calculate coverage gaps
    max_gap = int(np.ceil(k))
    avg_gap = k

    # Calculate how evenly distributed the sample is
    # Perfect coverage would have exactly k spacing
    spacing_variance = 0  # In systematic sampling, spacing is constant

    results = {
        'population_size': population_size,
        'sample_size': sample_size,
        'sampling_interval': k,
        'max_gap_between_samples': max_gap,
        'avg_gap_between_samples': avg_gap,
        'spacing_variance': spacing_variance,
        'coverage_quality': 'Uniform' if k == int(k) else 'Near-uniform'
    }

    return results


def compare_with_simple_random(
    df: pd.DataFrame,
    systematic_sample: pd.DataFrame,
    check_columns: list
) -> pd.DataFrame:
    """
    Compare systematic sample with what simple random sampling would give.

    Args:
        df: Full population DataFrame
        systematic_sample: Systematic sample
        check_columns: Columns to compare

    Returns:
        DataFrame with comparison

    Example:
        >>> comparison = compare_with_simple_random(
        ...     df, sample, ['age', 'income', 'conversion_rate']
        ... )
    """
    comparisons = []

    for col in check_columns:
        if col not in df.columns or col not in systematic_sample.columns:
            continue

        if pd.api.types.is_numeric_dtype(df[col]):
            pop_mean = df[col].mean()
            samp_mean = systematic_sample[col].mean()
            pop_std = df[col].std()

            # Standardized difference
            std_diff = (samp_mean - pop_mean) / pop_std if pop_std > 0 else 0

            comparisons.append({
                'variable': col,
                'population_mean': pop_mean,
                'sample_mean': samp_mean,
                'difference': samp_mean - pop_mean,
                'standardized_diff': std_diff,
                'representative': 'Yes' if abs(std_diff) < 0.1 else 'Check'
            })

    comparison_df = pd.DataFrame(comparisons)

    return comparison_df


def run(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Run systematic sampling based on configuration.

    Args:
        config: Configuration dictionary with parameters

    Returns:
        Systematic sample DataFrame

    Example:
        >>> config = {
        ...     'data_path': 'data/raw/ecommerce_data.csv',
        ...     'sample_size': 1000,
        ...     'random_seed': 42,
        ...     'check_periodicity': True,
        ...     'periodicity_columns': ['total_orders', 'conversion_rate']
        ... }
        >>> sample = run(config)
    """
    print("\n" + "="*70)
    print("SYSTEMATIC SAMPLING")
    print("="*70)

    # Validate configuration
    required_keys = ['data_path', 'sample_size']
    optional_keys = {
        'random_start': None,
        'random_seed': 42,
        'output_path': None,
        'check_periodicity': True,
        'periodicity_columns': ['total_orders', 'avg_order_value'],
        'max_period': 50,
        'assess_representativeness': True,
        'check_columns': ['age', 'total_orders', 'avg_order_value', 'conversion_rate']
    }

    config = validate_config(config, required_keys, optional_keys)

    # Load data
    print(f"\nLoading data from: {config['data_path']}")
    df = load_data(config['data_path'])

    # Check for periodicity (warning if found)
    if config['check_periodicity'] and config['periodicity_columns']:
        print(f"\nChecking for periodicity in data...")

        for col in config['periodicity_columns']:
            if col in df.columns:
                periodicity = detect_periodicity(df, col, max_period=config['max_period'])

                if periodicity['periodic']:
                    warnings.warn(
                        f"\nPeriodicity detected in '{col}'!\n"
                        f"  Period: {periodicity['period']}\n"
                        f"  Correlation: {periodicity['max_correlation']:.3f}\n"
                        f"  Systematic sampling may be biased. Consider:\n"
                        f"  - Using stratified sampling instead\n"
                        f"  - Randomizing data order before systematic sampling\n"
                        f"  - Avoiding sampling interval near detected period",
                        UserWarning
                    )
                else:
                    print(f"  {col}: No strong periodicity detected")

    # Perform systematic sampling
    print(f"\nPerforming systematic sampling...")

    sample = systematic_sample(
        df,
        sample_size=config['sample_size'],
        random_start=config['random_start'],
        random_seed=config['random_seed']
    )

    # Assess coverage
    k = len(df) / config['sample_size']
    coverage = assess_systematic_coverage(len(df), config['sample_size'], k)

    print(f"\nSampling Coverage:")
    print(f"  Sampling interval: {coverage['sampling_interval']:.2f}")
    print(f"  Coverage quality: {coverage['coverage_quality']}")

    # Assess representativeness
    if config['assess_representativeness']:
        print(f"\nAssessing sample representativeness...")

        comparison = compare_with_simple_random(
            df, sample, config['check_columns']
        )

        if not comparison.empty:
            print("\nRepresentativeness Check:")
            display_cols = ['variable', 'population_mean', 'sample_mean',
                           'standardized_diff', 'representative']
            print(comparison[display_cols].to_string(index=False))

            rep_count = (comparison['representative'] == 'Yes').sum()
            total_count = len(comparison)
            print(f"\n  Representative variables: {rep_count}/{total_count}")

    # Save output if path provided
    if config['output_path']:
        save_data(sample, config['output_path'])

    print("\n" + "="*70)
    print("[SUCCESS] Systematic sampling complete!")
    print("="*70 + "\n")

    return sample


def main():
    """Main function for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Systematic Sampling')
    parser.add_argument('--config', type=str, required=True,
                        help='Path to JSON configuration file')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Run sampling
    sample = run(config)


if __name__ == "__main__":
    # If no command-line args, run example
    if len(sys.argv) == 1:
        print("Running example with default configuration...")

        config = {
            'data_path': '../../data/raw/ecommerce_data.csv',
            'sample_size': 1000,
            'random_seed': 42,
            'check_periodicity': True,
            'periodicity_columns': ['total_orders', 'avg_order_value'],
            'assess_representativeness': True,
            'check_columns': ['age', 'total_orders', 'avg_order_value', 'conversion_rate']
        }

        sample = run(config)
    else:
        main()
