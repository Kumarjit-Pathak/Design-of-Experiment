"""
Cluster Sampling Module

This module implements cluster (two-stage) sampling where the population is
divided into clusters, clusters are randomly selected, and then all or some
elements within selected clusters are sampled. This is cost-effective when
clusters are geographically or logistically convenient.

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union
import sys
import os
import warnings

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config_loader import load_config, validate_config
from utils.data_loader import load_data, save_data, print_data_summary


def cluster_sample(
    df: pd.DataFrame,
    cluster_by: str,
    n_clusters: Optional[int] = None,
    cluster_sample_size: Optional[int] = None,
    within_cluster_sampling: str = 'all',
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Perform two-stage cluster sampling.

    Stage 1: Randomly select clusters
    Stage 2: Sample elements within selected clusters (all or subsample)

    Args:
        df: DataFrame to sample from
        cluster_by: Column name defining clusters (e.g., 'location', 'store_id')
        n_clusters: Number of clusters to select (if None, calculated from cluster_sample_size)
        cluster_sample_size: Total sample size desired (if None, uses n_clusters)
        within_cluster_sampling: 'all' or 'proportional' or integer for fixed size
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame containing cluster sample

    Example:
        >>> sample = cluster_sample(
        ...     df,
        ...     cluster_by='location',
        ...     n_clusters=10,
        ...     within_cluster_sampling='all'
        ... )
    """
    # Set random seed
    if random_seed is not None:
        np.random.seed(random_seed)

    # Validate cluster column
    if cluster_by not in df.columns:
        raise ValueError(f"Cluster column '{cluster_by}' not found in DataFrame")

    # Get unique clusters and their sizes
    cluster_sizes = df[cluster_by].value_counts()
    total_clusters = len(cluster_sizes)

    print(f"[INFO] Total clusters: {total_clusters}")
    print(f"[INFO] Cluster sizes: min={cluster_sizes.min()}, "
          f"max={cluster_sizes.max()}, mean={cluster_sizes.mean():.1f}")

    # Determine number of clusters to select
    if n_clusters is None and cluster_sample_size is None:
        raise ValueError("Must specify either n_clusters or cluster_sample_size")

    if n_clusters is None:
        # Estimate from desired sample size
        avg_cluster_size = cluster_sizes.mean()
        n_clusters = max(1, int(cluster_sample_size / avg_cluster_size))

    n_clusters = min(n_clusters, total_clusters)

    # Stage 1: Select clusters randomly
    selected_clusters = np.random.choice(
        cluster_sizes.index,
        size=n_clusters,
        replace=False
    )

    print(f"[INFO] Selected {n_clusters} clusters: {list(selected_clusters)}")

    # Stage 2: Sample within clusters
    samples = []

    for cluster in selected_clusters:
        cluster_data = df[df[cluster_by] == cluster]

        if within_cluster_sampling == 'all':
            # Take all elements from selected clusters
            cluster_sample = cluster_data

        elif within_cluster_sampling == 'proportional':
            # Sample proportionally to cluster size
            if cluster_sample_size:
                prop = len(cluster_data) / df[df[cluster_by].isin(selected_clusters)].shape[0]
                n_from_cluster = int(cluster_sample_size * prop)
                n_from_cluster = min(n_from_cluster, len(cluster_data))
            else:
                n_from_cluster = len(cluster_data)

            cluster_sample = cluster_data.sample(n=n_from_cluster, random_state=random_seed)

        elif isinstance(within_cluster_sampling, int):
            # Fixed number from each cluster
            n_from_cluster = min(within_cluster_sampling, len(cluster_data))
            cluster_sample = cluster_data.sample(n=n_from_cluster, random_state=random_seed)

        else:
            raise ValueError(f"Invalid within_cluster_sampling: {within_cluster_sampling}")

        samples.append(cluster_sample)

    # Combine samples
    final_sample = pd.concat(samples, ignore_index=True)

    print(f"[OK] Cluster sample generated: {len(final_sample):,} observations")

    return final_sample


def calculate_design_effect(
    population: pd.DataFrame,
    cluster_by: str,
    outcome_var: str
) -> Dict[str, float]:
    """
    Calculate design effect (DEFF) due to clustering.

    DEFF measures the loss of efficiency compared to simple random sampling.
    DEFF = 1 + (m - 1) * ICC
    where m = average cluster size, ICC = intraclass correlation

    Args:
        population: Full population DataFrame
        cluster_by: Cluster identifier column
        outcome_var: Outcome variable to analyze

    Returns:
        Dictionary with design effect metrics

    Example:
        >>> deff_results = calculate_design_effect(df, 'location', 'conversion_rate')
    """
    if outcome_var not in population.columns:
        raise ValueError(f"Outcome variable '{outcome_var}' not found")

    if not pd.api.types.is_numeric_dtype(population[outcome_var]):
        raise ValueError(f"Outcome variable '{outcome_var}' must be numerical")

    # Calculate ICC (Intraclass Correlation Coefficient)
    # This measures how similar observations within clusters are

    # Overall variance
    grand_mean = population[outcome_var].mean()
    total_variance = population[outcome_var].var()

    # Between-cluster variance
    cluster_means = population.groupby(cluster_by)[outcome_var].mean()
    cluster_sizes = population.groupby(cluster_by).size()
    between_var = ((cluster_means - grand_mean) ** 2 * cluster_sizes).sum() / (len(population) - 1)

    # Within-cluster variance
    within_var = total_variance - between_var

    # ICC
    icc = between_var / (between_var + within_var) if (between_var + within_var) > 0 else 0

    # Average cluster size
    avg_cluster_size = cluster_sizes.mean()

    # Design effect
    deff = 1 + (avg_cluster_size - 1) * icc

    # Effective sample size
    # If you have n observations, due to clustering, the effective sample size is n / DEFF
    n_actual = len(population)
    n_effective = n_actual / deff if deff > 0 else n_actual

    results = {
        'icc': icc,
        'avg_cluster_size': avg_cluster_size,
        'design_effect': deff,
        'efficiency_loss_pct': (deff - 1) * 100,
        'effective_sample_multiplier': 1 / deff if deff > 0 else 1.0,
        'interpretation': 'High clustering effect' if icc > 0.05
                         else 'Moderate clustering effect' if icc > 0.01
                         else 'Low clustering effect'
    }

    return results


def assess_cluster_homogeneity(
    df: pd.DataFrame,
    cluster_by: str,
    outcome_vars: list
) -> pd.DataFrame:
    """
    Assess homogeneity within clusters for multiple outcome variables.

    Args:
        df: DataFrame with cluster data
        cluster_by: Cluster identifier column
        outcome_vars: List of outcome variables to assess

    Returns:
        DataFrame with homogeneity metrics per outcome

    Example:
        >>> homogeneity = assess_cluster_homogeneity(
        ...     df, 'location', ['conversion_rate', 'lifetime_value']
        ... )
    """
    results = []

    for var in outcome_vars:
        if var not in df.columns or not pd.api.types.is_numeric_dtype(df[var]):
            continue

        # Calculate coefficient of variation within each cluster
        cluster_stats = df.groupby(cluster_by)[var].agg(['mean', 'std', 'count'])
        cluster_stats['cv'] = cluster_stats['std'] / cluster_stats['mean']

        # Overall statistics
        overall_cv = df[var].std() / df[var].mean() if df[var].mean() != 0 else np.nan

        # Calculate ICC
        deff_results = calculate_design_effect(df, cluster_by, var)

        results.append({
            'outcome_variable': var,
            'icc': deff_results['icc'],
            'design_effect': deff_results['design_effect'],
            'avg_cluster_mean': cluster_stats['mean'].mean(),
            'std_of_cluster_means': cluster_stats['mean'].std(),
            'avg_within_cluster_cv': cluster_stats['cv'].mean(),
            'overall_cv': overall_cv,
            'homogeneity': 'High' if deff_results['icc'] > 0.05
                          else 'Moderate' if deff_results['icc'] > 0.01
                          else 'Low'
        })

    results_df = pd.DataFrame(results)

    return results_df


def compare_cluster_characteristics(
    population: pd.DataFrame,
    sample: pd.DataFrame,
    cluster_by: str,
    comparison_vars: list
) -> pd.DataFrame:
    """
    Compare characteristics of selected vs non-selected clusters.

    Args:
        population: Full population DataFrame
        sample: Cluster sample DataFrame
        cluster_by: Cluster identifier column
        comparison_vars: Variables to compare

    Returns:
        DataFrame with comparison

    Example:
        >>> comparison = compare_cluster_characteristics(
        ...     df, sample, 'location', ['age', 'income', 'conversion_rate']
        ... )
    """
    selected_clusters = sample[cluster_by].unique()

    comparisons = []

    for var in comparison_vars:
        if var not in population.columns or not pd.api.types.is_numeric_dtype(population[var]):
            continue

        # Selected clusters
        selected_data = population[population[cluster_by].isin(selected_clusters)][var]
        # Non-selected clusters
        non_selected_data = population[~population[cluster_by].isin(selected_clusters)][var]

        comparisons.append({
            'variable': var,
            'selected_mean': selected_data.mean(),
            'non_selected_mean': non_selected_data.mean() if len(non_selected_data) > 0 else np.nan,
            'difference': selected_data.mean() - (non_selected_data.mean() if len(non_selected_data) > 0 else 0),
            'selected_std': selected_data.std(),
            'non_selected_std': non_selected_data.std() if len(non_selected_data) > 0 else np.nan
        })

    comparison_df = pd.DataFrame(comparisons)

    return comparison_df


def run(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Run cluster sampling based on configuration.

    Args:
        config: Configuration dictionary with parameters

    Returns:
        Cluster sample DataFrame

    Example:
        >>> config = {
        ...     'data_path': 'data/raw/ecommerce_data.csv',
        ...     'cluster_by': 'location',
        ...     'n_clusters': 2,
        ...     'within_cluster_sampling': 'all',
        ...     'random_seed': 42
        ... }
        >>> sample = run(config)
    """
    print("\n" + "="*70)
    print("CLUSTER SAMPLING")
    print("="*70)

    # Validate configuration
    required_keys = ['data_path', 'cluster_by']
    optional_keys = {
        'n_clusters': None,
        'cluster_sample_size': None,
        'within_cluster_sampling': 'all',
        'random_seed': 42,
        'output_path': None,
        'calculate_design_effect_var': 'conversion_rate',
        'assess_homogeneity': True,
        'homogeneity_vars': ['conversion_rate', 'lifetime_value', 'churn_probability'],
        'compare_clusters': True,
        'comparison_vars': ['age', 'total_orders', 'avg_order_value']
    }

    config = validate_config(config, required_keys, optional_keys)

    # Load data
    print(f"\nLoading data from: {config['data_path']}")
    df = load_data(config['data_path'])

    # Validate cluster column
    if config['cluster_by'] not in df.columns:
        raise ValueError(f"Cluster column '{config['cluster_by']}' not found")

    # Calculate design effect (before sampling)
    if config['calculate_design_effect_var'] and \
       config['calculate_design_effect_var'] in df.columns:
        print(f"\nCalculating design effect...")

        deff_results = calculate_design_effect(
            df,
            config['cluster_by'],
            config['calculate_design_effect_var']
        )

        print(f"\nDesign Effect Analysis (outcome: {config['calculate_design_effect_var']}):")
        print(f"  ICC (Intraclass Correlation): {deff_results['icc']:.4f}")
        print(f"  Average cluster size: {deff_results['avg_cluster_size']:.1f}")
        print(f"  Design Effect (DEFF): {deff_results['design_effect']:.4f}")
        print(f"  Efficiency loss: {deff_results['efficiency_loss_pct']:.2f}%")
        print(f"  {deff_results['interpretation']}")

        if deff_results['icc'] > 0.05:
            warnings.warn(
                "\nHigh ICC detected! Cluster sampling may be inefficient.\n"
                "Consider:\n"
                "- Selecting more clusters with fewer elements per cluster\n"
                "- Using stratified sampling instead\n"
                "- Increasing sample size to compensate for design effect",
                UserWarning
            )

    # Assess cluster homogeneity
    if config['assess_homogeneity'] and config['homogeneity_vars']:
        print(f"\nAssessing cluster homogeneity...")

        homogeneity = assess_cluster_homogeneity(
            df,
            config['cluster_by'],
            config['homogeneity_vars']
        )

        print("\nCluster Homogeneity:")
        print(homogeneity.to_string(index=False))

    # Perform cluster sampling
    print(f"\nPerforming cluster sampling...")
    print(f"  Cluster by: {config['cluster_by']}")
    print(f"  Within-cluster sampling: {config['within_cluster_sampling']}")

    sample = cluster_sample(
        df,
        cluster_by=config['cluster_by'],
        n_clusters=config['n_clusters'],
        cluster_sample_size=config['cluster_sample_size'],
        within_cluster_sampling=config['within_cluster_sampling'],
        random_seed=config['random_seed']
    )

    # Compare selected vs non-selected clusters
    if config['compare_clusters'] and config['comparison_vars']:
        print(f"\nComparing selected vs non-selected clusters...")

        comparison = compare_cluster_characteristics(
            df, sample, config['cluster_by'], config['comparison_vars']
        )

        print("\nCluster Comparison:")
        print(comparison.to_string(index=False))

    # Save output if path provided
    if config['output_path']:
        save_data(sample, config['output_path'])

    print("\n" + "="*70)
    print("[SUCCESS] Cluster sampling complete!")
    print("="*70 + "\n")

    return sample


def main():
    """Main function for command-line execution."""
    import argparse

    parser = argparse.ArgumentParser(description='Cluster Sampling')
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
            'cluster_by': 'location',  # Urban, Suburban, Rural
            'n_clusters': 2,
            'within_cluster_sampling': 'all',
            'random_seed': 42,
            'calculate_design_effect_var': 'conversion_rate',
            'assess_homogeneity': True,
            'homogeneity_vars': ['conversion_rate', 'lifetime_value', 'churn_probability'],
            'compare_clusters': True,
            'comparison_vars': ['age', 'total_orders', 'avg_order_value']
        }

        sample = run(config)
    else:
        main()
