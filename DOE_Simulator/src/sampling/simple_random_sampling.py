"""
Simple Random Sampling Module

This module implements simple random sampling where each unit has an equal
probability of selection. This is the foundation of probability sampling and
eliminates selection bias when properly executed.

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import load_config, validate_config
from utils.data_loader import load_data, save_data, print_data_summary


def simple_random_sample(
    df: pd.DataFrame,
    sample_size: int,
    random_seed: Optional[int] = None,
    replace: bool = False
) -> pd.DataFrame:
    """
    Perform simple random sampling without replacement.

    Each observation has an equal probability of selection: P = n/N
    where n = sample size, N = population size.

    Args:
        df: DataFrame to sample from
        sample_size: Number of observations to sample
        random_seed: Random seed for reproducibility
        replace: Whether to sample with replacement (default False)

    Returns:
        DataFrame containing sampled observations

    Example:
        >>> df_sample = simple_random_sample(df, sample_size=1000, random_seed=42)
    """
    # Validate sample size
    if sample_size > len(df) and not replace:
        print(f"[WARNING] Sample size ({sample_size}) exceeds population size ({len(df)})")
        print(f"[INFO] Using full dataset (n={len(df)})")
        sample_size = len(df)

    # Set random seed if provided
    if random_seed is not None:
        np.random.seed(random_seed)

    # Perform sampling
    sample = df.sample(n=sample_size, replace=replace, random_state=random_seed)

    print(f"[OK] Simple random sample generated")
    print(f"     Population size: {len(df):,}")
    print(f"     Sample size: {len(sample):,}")
    print(f"     Sampling fraction: {len(sample)/len(df)*100:.2f}%")

    return sample


def calculate_sampling_probabilities(
    population_size: int,
    sample_size: int
) -> Dict[str, float]:
    """
    Calculate sampling probabilities for simple random sampling.

    Args:
        population_size: Size of population (N)
        sample_size: Size of sample (n)

    Returns:
        Dictionary with probability calculations

    Example:
        >>> probs = calculate_sampling_probabilities(20000, 1000)
        >>> print(f"Selection probability: {probs['p_selection']}")
    """
    p_selection = sample_size / population_size
    p_not_selection = 1 - p_selection

    # Standard error of proportion (if estimating population proportion)
    # SE(p) = sqrt(p * (1-p) / n) for large populations
    se_proportion = np.sqrt(0.5 * 0.5 / sample_size)  # Worst case: p=0.5

    results = {
        'population_size': population_size,
        'sample_size': sample_size,
        'p_selection': p_selection,
        'p_not_selection': p_not_selection,
        'sampling_fraction': p_selection * 100,
        'se_proportion_worst_case': se_proportion
    }

    return results


def assess_sample_representativeness(
    population: pd.DataFrame,
    sample: pd.DataFrame,
    check_columns: Optional[list] = None
) -> pd.DataFrame:
    """
    Compare sample and population distributions to assess representativeness.

    Args:
        population: Full population DataFrame
        sample: Sample DataFrame
        check_columns: List of columns to check (None = all numerical)

    Returns:
        DataFrame with comparison statistics

    Example:
        >>> comparison = assess_sample_representativeness(df, sample, ['age', 'income'])
    """
    if check_columns is None:
        check_columns = population.select_dtypes(include=[np.number]).columns.tolist()

    comparisons = []

    for col in check_columns:
        if col not in population.columns or col not in sample.columns:
            continue

        # Numerical variables
        if pd.api.types.is_numeric_dtype(population[col]):
            pop_mean = population[col].mean()
            samp_mean = sample[col].mean()
            pop_std = population[col].std()
            samp_std = sample[col].std()

            # Standardized difference
            std_diff = (samp_mean - pop_mean) / pop_std if pop_std > 0 else 0

            comparisons.append({
                'variable': col,
                'type': 'numerical',
                'pop_mean': pop_mean,
                'sample_mean': samp_mean,
                'difference': samp_mean - pop_mean,
                'pop_std': pop_std,
                'sample_std': samp_std,
                'standardized_diff': std_diff,
                'representative': 'Yes' if abs(std_diff) < 0.1 else 'Check'
            })

        # Categorical variables
        else:
            pop_dist = population[col].value_counts(normalize=True)
            samp_dist = sample[col].value_counts(normalize=True)

            # Chi-square test would go here
            comparisons.append({
                'variable': col,
                'type': 'categorical',
                'pop_distribution': str(pop_dist.to_dict()),
                'sample_distribution': str(samp_dist.to_dict())
            })

    comparison_df = pd.DataFrame(comparisons)

    return comparison_df


def run(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Run simple random sampling based on configuration.

    Args:
        config: Configuration dictionary with parameters

    Returns:
        Sampled DataFrame

    Example:
        >>> config = {
        ...     'data_path': 'data/raw/ecommerce_data.csv',
        ...     'sample_size': 1000,
        ...     'random_seed': 42,
        ...     'output_path': 'data/processed/sample.csv'
        ... }
        >>> sample = run(config)
    """
    print("\n" + "="*70)
    print("SIMPLE RANDOM SAMPLING")
    print("="*70)

    # Validate configuration
    required_keys = ['data_path', 'sample_size']
    optional_keys = {
        'random_seed': 42,
        'replace': False,
        'output_path': None,
        'assess_representativeness': True,
        'check_columns': None
    }

    config = validate_config(config, required_keys, optional_keys)

    # Load data
    print(f"\nLoading data from: {config['data_path']}")
    df = load_data(config['data_path'])

    # Calculate sampling probabilities
    probs = calculate_sampling_probabilities(len(df), config['sample_size'])
    print(f"\nSampling Probabilities:")
    print(f"  Selection probability: {probs['p_selection']:.4f}")
    print(f"  Sampling fraction: {probs['sampling_fraction']:.2f}%")

    # Perform sampling
    print(f"\nPerforming simple random sampling...")
    sample = simple_random_sample(
        df,
        sample_size=config['sample_size'],
        random_seed=config['random_seed'],
        replace=config['replace']
    )

    # Assess representativeness
    if config['assess_representativeness']:
        print(f"\nAssessing sample representativeness...")
        comparison = assess_sample_representativeness(
            df,
            sample,
            check_columns=config['check_columns']
        )

        # Display numerical comparisons
        numerical_comp = comparison[comparison['type'] == 'numerical']
        if not numerical_comp.empty:
            print("\nRepresentativeness Check (Numerical Variables):")
            display_cols = ['variable', 'pop_mean', 'sample_mean', 'standardized_diff', 'representative']
            print(numerical_comp[display_cols].to_string(index=False))

            # Count representative variables
            rep_count = (numerical_comp['representative'] == 'Yes').sum()
            total_count = len(numerical_comp)
            print(f"\n  Representative variables: {rep_count}/{total_count}")

    # Save output if path provided
    if config['output_path']:
        save_data(sample, config['output_path'])

    print("\n" + "="*70)
    print("[SUCCESS] Simple random sampling complete!")
    print("="*70 + "\n")

    return sample


def main():
    """Main function for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Simple Random Sampling')
    parser.add_argument('--config', type=str, required=True,
                        help='Path to JSON configuration file')

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Run sampling
    sample = run(config)

    # Display sample summary
    print_data_summary(sample)


if __name__ == "__main__":
    # If no command-line args, run example
    if len(sys.argv) == 1:
        print("Running example with default configuration...")

        config = {
            'data_path': '../../data/raw/ecommerce_data.csv',
            'sample_size': 1000,
            'random_seed': 42,
            'replace': False,
            'assess_representativeness': True,
            'check_columns': ['age', 'total_orders', 'avg_order_value', 'conversion_rate']
        }

        sample = run(config)
    else:
        main()
