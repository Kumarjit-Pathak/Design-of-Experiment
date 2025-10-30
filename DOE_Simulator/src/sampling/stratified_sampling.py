"""
Stratified Random Sampling Module

This module implements stratified random sampling where the population is divided
into homogeneous subgroups (strata) and random samples are drawn from each stratum.
This improves precision and ensures representation of all subgroups.

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import load_config, validate_config
from utils.data_loader import load_data, save_data, print_data_summary
from utils.statistical_tests import calculate_cohens_d


def stratified_random_sample(
    df: pd.DataFrame,
    stratify_by: Union[str, list],
    sample_size: int,
    allocation: str = 'proportional',
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform stratified random sampling.

    Args:
        df: DataFrame to sample from
        stratify_by: Column name(s) for stratification
        sample_size: Total sample size desired
        allocation: Allocation method - 'proportional', 'equal', or dict with stratum:n pairs
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame containing stratified sample

    Example:
        >>> sample = stratified_random_sample(
        ...     df,
        ...     stratify_by='income_level',
        ...     sample_size=1000,
        ...     allocation='proportional'
        ... )
    """
    # Set random seed
    if random_seed is not None:
        np.random.seed(random_seed)

    # Ensure stratify_by is a list
    if isinstance(stratify_by, str):
        stratify_by = [stratify_by]

    # Create strata identifier
    if len(stratify_by) == 1:
        df['_stratum'] = df[stratify_by[0]].astype(str)
    else:
        df['_stratum'] = df[stratify_by].astype(str).agg('_'.join, axis=1)

    # Get stratum sizes
    stratum_counts = df['_stratum'].value_counts()
    n_strata = len(stratum_counts)

    print(f"[INFO] Number of strata: {n_strata}")
    print(f"[INFO] Stratum sizes: {stratum_counts.to_dict()}")

    # Determine sample sizes per stratum
    if allocation == 'proportional':
        # Proportional allocation: n_h = n * (N_h / N)
        stratum_samples = {}
        for stratum, count in stratum_counts.items():
            n_h = int(np.round(sample_size * (count / len(df))))
            stratum_samples[stratum] = max(1, n_h)  # At least 1 per stratum

        # Adjust to match exact total (due to rounding)
        total_allocated = sum(stratum_samples.values())
        if total_allocated != sample_size:
            # Adjust largest stratum
            largest_stratum = stratum_counts.idxmax()
            stratum_samples[largest_stratum] += (sample_size - total_allocated)

    elif allocation == 'equal':
        # Equal allocation: same n from each stratum
        n_per_stratum = sample_size // n_strata
        remainder = sample_size % n_strata
        stratum_samples = {}

        for i, stratum in enumerate(stratum_counts.index):
            n_h = n_per_stratum + (1 if i < remainder else 0)
            # Can't sample more than available
            n_h = min(n_h, stratum_counts[stratum])
            stratum_samples[stratum] = n_h

    elif isinstance(allocation, dict):
        # Custom allocation provided
        stratum_samples = allocation

    else:
        raise ValueError(f"Unknown allocation method: {allocation}")

    # Sample from each stratum
    samples = []
    for stratum, n_h in stratum_samples.items():
        stratum_data = df[df['_stratum'] == stratum]

        if n_h > len(stratum_data):
            print(f"[WARNING] Requested {n_h} from stratum '{stratum}' "
                  f"but only {len(stratum_data)} available. Using all.")
            n_h = len(stratum_data)

        stratum_sample = stratum_data.sample(n=n_h, random_state=random_seed)
        samples.append(stratum_sample)

    # Combine samples
    final_sample = pd.concat(samples, ignore_index=True)

    # Remove temporary stratum column
    final_sample = final_sample.drop(columns=['_stratum'])
    df = df.drop(columns=['_stratum'])

    print(f"[OK] Stratified sample generated")
    print(f"     Total sample size: {len(final_sample):,}")
    print(f"     Allocation method: {allocation}")

    return final_sample


def calculate_stratification_efficiency(
    population: pd.DataFrame,
    sample: pd.DataFrame,
    stratify_by: str,
    outcome_var: str
) -> Dict[str, float]:
    """
    Calculate the efficiency of stratification compared to simple random sampling.

    Args:
        population: Full population DataFrame
        sample: Stratified sample DataFrame
        stratify_by: Stratification variable
        outcome_var: Outcome variable of interest

    Returns:
        Dictionary with efficiency metrics

    Example:
        >>> efficiency = calculate_stratification_efficiency(
        ...     df, sample, 'income_level', 'conversion_rate'
        ... )
    """
    # Variance within strata
    strata_variances = []
    strata_sizes = []

    for stratum in population[stratify_by].unique():
        stratum_data = population[population[stratify_by] == stratum][outcome_var]
        if len(stratum_data) > 1:
            strata_variances.append(stratum_data.var())
            strata_sizes.append(len(stratum_data))

    # Weighted average of within-stratum variances
    total_n = sum(strata_sizes)
    weights = [n / total_n for n in strata_sizes]
    var_within = sum(w * v for w, v in zip(weights, strata_variances))

    # Total variance (for simple random sampling)
    var_total = population[outcome_var].var()

    # Design effect (deff) - ratio of variances
    # deff < 1 means stratification is more efficient
    design_effect = var_within / var_total if var_total > 0 else 1.0

    # Relative efficiency
    relative_efficiency = 1 / design_effect

    results = {
        'variance_within_strata': var_within,
        'variance_total': var_total,
        'design_effect': design_effect,
        'relative_efficiency': relative_efficiency,
        'efficiency_gain_pct': (relative_efficiency - 1) * 100,
        'interpretation': 'More efficient than SRS' if design_effect < 1
                         else 'Less efficient than SRS'
    }

    return results


def assess_stratification_balance(
    population: pd.DataFrame,
    sample: pd.DataFrame,
    stratify_by: str
) -> pd.DataFrame:
    """
    Assess how well the sample represents population strata.

    Args:
        population: Full population DataFrame
        sample: Stratified sample DataFrame
        stratify_by: Stratification variable

    Returns:
        DataFrame with balance assessment

    Example:
        >>> balance = assess_stratification_balance(df, sample, 'income_level')
    """
    pop_dist = population[stratify_by].value_counts(normalize=True).sort_index()
    samp_dist = sample[stratify_by].value_counts(normalize=True).sort_index()

    # Combine into comparison DataFrame
    comparison = pd.DataFrame({
        'stratum': pop_dist.index,
        'population_pct': pop_dist.values * 100,
        'sample_pct': samp_dist.values * 100,
        'population_n': population[stratify_by].value_counts().sort_index().values,
        'sample_n': sample[stratify_by].value_counts().sort_index().values
    })

    comparison['difference_pct'] = comparison['sample_pct'] - comparison['population_pct']
    comparison['abs_difference'] = comparison['difference_pct'].abs()

    # Flag large discrepancies (>5% difference)
    comparison['balanced'] = comparison['abs_difference'] < 5.0

    return comparison


def calculate_stratum_statistics(
    sample: pd.DataFrame,
    stratify_by: str,
    outcome_vars: list
) -> pd.DataFrame:
    """
    Calculate statistics for each stratum.

    Args:
        sample: Stratified sample DataFrame
        stratify_by: Stratification variable
        outcome_vars: List of outcome variables to summarize

    Returns:
        DataFrame with stratum-level statistics

    Example:
        >>> stats = calculate_stratum_statistics(
        ...     sample, 'income_level', ['conversion_rate', 'lifetime_value']
        ... )
    """
    results = []

    for stratum in sample[stratify_by].unique():
        stratum_data = sample[sample[stratify_by] == stratum]

        result = {
            'stratum': stratum,
            'n': len(stratum_data)
        }

        for var in outcome_vars:
            if var in stratum_data.columns and pd.api.types.is_numeric_dtype(stratum_data[var]):
                result[f'{var}_mean'] = stratum_data[var].mean()
                result[f'{var}_std'] = stratum_data[var].std()
                result[f'{var}_median'] = stratum_data[var].median()

        results.append(result)

    stats_df = pd.DataFrame(results)

    return stats_df


def run(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Run stratified random sampling based on configuration.

    Args:
        config: Configuration dictionary with parameters

    Returns:
        Stratified sample DataFrame

    Example:
        >>> config = {
        ...     'data_path': 'data/raw/ecommerce_data.csv',
        ...     'stratify_by': 'income_level',
        ...     'sample_size': 1000,
        ...     'allocation': 'proportional',
        ...     'random_seed': 42
        ... }
        >>> sample = run(config)
    """
    print("\n" + "="*70)
    print("STRATIFIED RANDOM SAMPLING")
    print("="*70)

    # Validate configuration
    required_keys = ['data_path', 'stratify_by', 'sample_size']
    optional_keys = {
        'allocation': 'proportional',
        'random_seed': 42,
        'output_path': None,
        'assess_balance': True,
        'calculate_efficiency': True,
        'efficiency_outcome_var': 'conversion_rate',
        'outcome_vars': ['conversion_rate', 'lifetime_value']
    }

    config = validate_config(config, required_keys, optional_keys)

    # Load data
    print(f"\nLoading data from: {config['data_path']}")
    df = load_data(config['data_path'])

    # Validate stratification variable
    if isinstance(config['stratify_by'], str):
        if config['stratify_by'] not in df.columns:
            raise ValueError(f"Stratification variable '{config['stratify_by']}' not found")
    else:
        missing = [col for col in config['stratify_by'] if col not in df.columns]
        if missing:
            raise ValueError(f"Stratification variables not found: {missing}")

    # Perform stratified sampling
    print(f"\nPerforming stratified random sampling...")
    print(f"  Stratify by: {config['stratify_by']}")
    print(f"  Allocation: {config['allocation']}")

    sample = stratified_random_sample(
        df,
        stratify_by=config['stratify_by'],
        sample_size=config['sample_size'],
        allocation=config['allocation'],
        random_seed=config['random_seed']
    )

    # Assess stratification balance
    if config['assess_balance']:
        print(f"\nAssessing stratification balance...")
        stratify_var = config['stratify_by'] if isinstance(config['stratify_by'], str) \
                      else config['stratify_by'][0]

        balance = assess_stratification_balance(df, sample, stratify_var)
        print("\nStratum Balance:")
        print(balance.to_string(index=False))

        balanced_count = balance['balanced'].sum()
        total_count = len(balance)
        print(f"\nBalanced strata: {balanced_count}/{total_count}")

    # Calculate efficiency
    if config['calculate_efficiency'] and config['efficiency_outcome_var'] in df.columns:
        print(f"\nCalculating stratification efficiency...")
        stratify_var = config['stratify_by'] if isinstance(config['stratify_by'], str) \
                      else config['stratify_by'][0]

        efficiency = calculate_stratification_efficiency(
            df, sample, stratify_var, config['efficiency_outcome_var']
        )

        print(f"\nStratification Efficiency (outcome: {config['efficiency_outcome_var']}):")
        print(f"  Design Effect: {efficiency['design_effect']:.4f}")
        print(f"  Relative Efficiency: {efficiency['relative_efficiency']:.4f}")
        print(f"  Efficiency Gain: {efficiency['efficiency_gain_pct']:.2f}%")
        print(f"  {efficiency['interpretation']}")

    # Calculate stratum statistics
    if config['outcome_vars']:
        print(f"\nStratum Statistics:")
        stratify_var = config['stratify_by'] if isinstance(config['stratify_by'], str) \
                      else config['stratify_by'][0]

        stats = calculate_stratum_statistics(sample, stratify_var, config['outcome_vars'])
        print(stats.to_string(index=False))

    # Save output if path provided
    if config['output_path']:
        save_data(sample, config['output_path'])

    print("\n" + "="*70)
    print("[SUCCESS] Stratified random sampling complete!")
    print("="*70 + "\n")

    return sample


def main():
    """Main function for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Stratified Random Sampling')
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
            'stratify_by': 'income_level',
            'sample_size': 1000,
            'allocation': 'proportional',
            'random_seed': 42,
            'assess_balance': True,
            'calculate_efficiency': True,
            'efficiency_outcome_var': 'conversion_rate',
            'outcome_vars': ['conversion_rate', 'lifetime_value', 'churn_probability']
        }

        sample = run(config)
    else:
        main()
