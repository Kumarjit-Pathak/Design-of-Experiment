"""
Randomized Block Design (RBD)

An experimental design that accounts for one source of systematic variation (blocking factor)
by grouping experimental units into homogeneous blocks, then randomizing treatments
within each block. This design is appropriate when:
- There's a known source of variation (nuisance factor) to control
- Experimental units can be grouped into homogeneous blocks
- Each block can accommodate all treatments

RBD increases precision by removing block-to-block variation from experimental error.

Mathematical Model:
    Y_ij = μ + τ_i + β_j + ε_ij

Where:
    Y_ij = observation for treatment i in block j
    μ = overall mean
    τ_i = effect of treatment i
    β_j = effect of block j (nuisance factor)
    ε_ij = random error (assumed N(0, σ²))

Advantages:
- Controls for one blocking factor
- More efficient than CRD when blocks are effective
- Reduces experimental error variance

Author: DOE Simulator Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class RandomizedBlockDesign:
    """
    Randomized Block Design (RBD) implementation.

    This class handles:
    - Treatment assignment within blocks
    - Block effectiveness analysis
    - Two-way ANOVA (treatment + block effects)
    - Relative efficiency calculation vs CRD
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize RBD designer.

        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        np.random.seed(random_seed)
        self.design_matrix = None
        self.design_info = {}

    def create_design(
        self,
        data: pd.DataFrame,
        treatments: List[str],
        block_col: str,
        treatment_col: str = 'treatment',
        replications: int = 1,
        check_completeness: bool = True
    ) -> pd.DataFrame:
        """
        Create a randomized block design by assigning treatments within blocks.

        Args:
            data: DataFrame containing experimental units with blocking variable
            treatments: List of treatment names/labels
            block_col: Name of the column containing block identifiers
            treatment_col: Name of the column to store treatment assignment
            replications: Number of replications per treatment within each block
            check_completeness: Whether to verify complete block structure

        Returns:
            DataFrame with treatment assignments added

        Raises:
            ValueError: If blocks are incomplete or insufficient units

        Example:
            >>> rbd = RandomizedBlockDesign(random_seed=42)
            >>> data = pd.DataFrame({
            ...     'unit_id': range(120),
            ...     'location': ['A']*40 + ['B']*40 + ['C']*40,  # blocks
            ...     'baseline': np.random.randn(120)
            ... })
            >>> treatments = ['Control', 'Treatment_A', 'Treatment_B', 'Treatment_C']
            >>> design = rbd.create_design(data, treatments, block_col='location')
        """
        if block_col not in data.columns:
            raise ValueError(f"Block column '{block_col}' not found in data")

        # Get unique blocks
        blocks = data[block_col].unique()
        n_blocks = len(blocks)
        n_treatments = len(treatments)

        logger.info(f"Creating RBD with {n_treatments} treatments across {n_blocks} blocks")

        # Check if each block has enough units
        required_per_block = n_treatments * replications
        design_df = data.copy()
        design_df[treatment_col] = None

        assignments = []

        for block in blocks:
            block_data = data[data[block_col] == block]
            n_units_in_block = len(block_data)

            if n_units_in_block < required_per_block:
                if check_completeness:
                    raise ValueError(
                        f"Block '{block}' has {n_units_in_block} units but needs "
                        f"{required_per_block} ({n_treatments} treatments × {replications} reps)"
                    )
                else:
                    logger.warning(
                        f"Block '{block}' has insufficient units. "
                        f"Assigning as many treatments as possible."
                    )

            # Create treatment assignment for this block
            block_treatments = treatments * replications

            # If more units than needed, randomly select which units to assign
            if n_units_in_block > required_per_block:
                block_indices = np.random.choice(
                    block_data.index,
                    size=required_per_block,
                    replace=False
                )
            else:
                block_indices = block_data.index[:required_per_block]

            # Randomize treatment order within block
            np.random.shuffle(block_treatments)

            # Assign treatments to selected units in this block
            for idx, treatment in zip(block_indices, block_treatments):
                design_df.loc[idx, treatment_col] = treatment

        # Store design information
        self.design_matrix = design_df
        self.design_info = {
            'design_type': 'Randomized Block Design (RBD)',
            'n_treatments': n_treatments,
            'n_blocks': n_blocks,
            'treatments': treatments,
            'blocks': list(blocks),
            'block_col': block_col,
            'treatment_col': treatment_col,
            'replications': replications,
            'random_seed': self.random_seed,
            'units_per_block': required_per_block,
            'total_units_assigned': (design_df[treatment_col].notna()).sum()
        }

        # Log summary
        for block in blocks:
            block_summary = design_df[design_df[block_col] == block][treatment_col].value_counts()
            logger.info(f"Block '{block}': {dict(block_summary)}")

        return design_df

    def analyze_design(
        self,
        design_df: pd.DataFrame,
        response_var: str,
        treatment_col: str = 'treatment',
        block_col: str = None
    ) -> Dict:
        """
        Perform two-way ANOVA analysis on RBD experimental results.

        Analyzes both treatment effects and block effects, providing:
        - Treatment F-test and p-value
        - Block F-test and p-value
        - Effect sizes for both factors
        - Relative efficiency vs CRD

        Args:
            design_df: DataFrame with treatment assignments, blocks, and response
            response_var: Name of the response variable column
            treatment_col: Name of the treatment column
            block_col: Name of the block column (if None, uses stored value)

        Returns:
            Dictionary containing two-way ANOVA results and efficiency metrics

        Example:
            >>> results = rbd.analyze_design(design_df, response_var='yield', block_col='location')
        """
        if block_col is None:
            block_col = self.design_info.get('block_col')
            if block_col is None:
                raise ValueError("Block column must be specified")

        # Remove missing values
        analysis_df = design_df[[treatment_col, block_col, response_var]].dropna()

        # Calculate grand mean
        grand_mean = analysis_df[response_var].mean()
        n = len(analysis_df)

        # Treatment statistics
        treatment_means = analysis_df.groupby(treatment_col)[response_var].mean()
        treatment_counts = analysis_df.groupby(treatment_col)[response_var].count()
        k = len(treatment_means)  # number of treatments

        # Block statistics
        block_means = analysis_df.groupby(block_col)[response_var].mean()
        block_counts = analysis_df.groupby(block_col)[response_var].count()
        b = len(block_means)  # number of blocks

        # Calculate Sum of Squares
        # SS Total
        ss_total = ((analysis_df[response_var] - grand_mean) ** 2).sum()

        # SS Treatment
        ss_treatment = sum(
            treatment_counts[t] * (treatment_means[t] - grand_mean) ** 2
            for t in treatment_means.index
        )

        # SS Block
        ss_block = sum(
            block_counts[blk] * (block_means[blk] - grand_mean) ** 2
            for blk in block_means.index
        )

        # SS Error (residual)
        ss_error = ss_total - ss_treatment - ss_block

        # Degrees of freedom
        df_treatment = k - 1
        df_block = b - 1
        df_error = (k - 1) * (b - 1)
        df_total = n - 1

        # Mean Squares
        ms_treatment = ss_treatment / df_treatment if df_treatment > 0 else 0
        ms_block = ss_block / df_block if df_block > 0 else 0
        ms_error = ss_error / df_error if df_error > 0 else 0

        # F-statistics
        f_treatment = ms_treatment / ms_error if ms_error > 0 else 0
        f_block = ms_block / ms_error if ms_error > 0 else 0

        # P-values
        p_treatment = 1 - stats.f.cdf(f_treatment, df_treatment, df_error) if f_treatment > 0 else 1.0
        p_block = 1 - stats.f.cdf(f_block, df_block, df_error) if f_block > 0 else 1.0

        # Effect sizes (Eta-squared)
        eta_sq_treatment = ss_treatment / ss_total if ss_total > 0 else 0
        eta_sq_block = ss_block / ss_total if ss_total > 0 else 0

        # Interpret effect sizes
        def interpret_effect(eta_sq):
            if eta_sq < 0.01:
                return "negligible"
            elif eta_sq < 0.06:
                return "small"
            elif eta_sq < 0.14:
                return "medium"
            else:
                return "large"

        # Calculate relative efficiency vs CRD
        # RE = (MS_block + (b-1) * MS_error) / (b * MS_error)
        if ms_error > 0:
            relative_efficiency = (ms_block + (b - 1) * ms_error) / (b * ms_error)
        else:
            relative_efficiency = 1.0

        # Treatment statistics by group
        treatment_stats = {}
        for treatment in treatment_means.index:
            group_data = analysis_df[analysis_df[treatment_col] == treatment][response_var]
            treatment_stats[treatment] = {
                'mean': group_data.mean(),
                'std': group_data.std(),
                'n': len(group_data),
                'se': group_data.sem()
            }

        # Block statistics
        block_stats = {}
        for block in block_means.index:
            group_data = analysis_df[analysis_df[block_col] == block][response_var]
            block_stats[block] = {
                'mean': group_data.mean(),
                'std': group_data.std(),
                'n': len(group_data)
            }

        results = {
            'design_type': 'RBD',
            'response_variable': response_var,
            'n_observations': n,
            'n_treatments': k,
            'n_blocks': b,
            'grand_mean': grand_mean,
            'anova_table': {
                'treatment': {
                    'ss': ss_treatment,
                    'df': df_treatment,
                    'ms': ms_treatment,
                    'f_statistic': f_treatment,
                    'p_value': p_treatment,
                    'significant': p_treatment < 0.05
                },
                'block': {
                    'ss': ss_block,
                    'df': df_block,
                    'ms': ms_block,
                    'f_statistic': f_block,
                    'p_value': p_block,
                    'significant': p_block < 0.05
                },
                'error': {
                    'ss': ss_error,
                    'df': df_error,
                    'ms': ms_error
                },
                'total': {
                    'ss': ss_total,
                    'df': df_total
                }
            },
            'effect_sizes': {
                'treatment_eta_squared': eta_sq_treatment,
                'treatment_interpretation': interpret_effect(eta_sq_treatment),
                'block_eta_squared': eta_sq_block,
                'block_interpretation': interpret_effect(eta_sq_block)
            },
            'relative_efficiency': {
                'vs_crd': relative_efficiency,
                'interpretation': 'RBD is more efficient' if relative_efficiency > 1 else 'CRD would be more efficient',
                'percent_improvement': (relative_efficiency - 1) * 100
            },
            'treatment_statistics': treatment_stats,
            'block_statistics': block_stats
        }

        # Logging
        logger.info(f"Two-way ANOVA Results:")
        logger.info(f"  Treatment: F({df_treatment}, {df_error}) = {f_treatment:.4f}, p = {p_treatment:.4f}")
        logger.info(f"  Block: F({df_block}, {df_error}) = {f_block:.4f}, p = {p_block:.4f}")
        logger.info(f"  Treatment effect size (η²) = {eta_sq_treatment:.4f} ({interpret_effect(eta_sq_treatment)})")
        logger.info(f"  Block effect size (η²) = {eta_sq_block:.4f} ({interpret_effect(eta_sq_block)})")
        logger.info(f"  Relative Efficiency vs CRD = {relative_efficiency:.2f} ({(relative_efficiency-1)*100:.1f}% {'improvement' if relative_efficiency > 1 else 'decrease'})")

        return results

    def check_block_effectiveness(
        self,
        design_df: pd.DataFrame,
        response_var: str,
        block_col: str
    ) -> Dict:
        """
        Assess whether blocking was effective in reducing variability.

        A block is effective if between-block variation is substantial compared
        to within-block variation.

        Args:
            design_df: DataFrame with blocks and response
            response_var: Name of response variable
            block_col: Name of block column

        Returns:
            Dictionary with block effectiveness metrics
        """
        analysis_df = design_df[[block_col, response_var]].dropna()

        # Overall variance
        total_variance = analysis_df[response_var].var()

        # Between-block variance
        block_means = analysis_df.groupby(block_col)[response_var].mean()
        grand_mean = analysis_df[response_var].mean()
        between_block_var = ((block_means - grand_mean) ** 2).mean()

        # Within-block variance
        within_block_vars = []
        for block in analysis_df[block_col].unique():
            block_data = analysis_df[analysis_df[block_col] == block][response_var]
            if len(block_data) > 1:
                within_block_vars.append(block_data.var())

        within_block_var = np.mean(within_block_vars) if within_block_vars else 0

        # Intraclass correlation (ICC)
        # Proportion of variance due to blocks
        if (between_block_var + within_block_var) > 0:
            icc = between_block_var / (between_block_var + within_block_var)
        else:
            icc = 0

        # Interpretation
        if icc > 0.25:
            effectiveness = "Highly effective - blocking explains substantial variation"
        elif icc > 0.10:
            effectiveness = "Moderately effective - blocking explains some variation"
        elif icc > 0.05:
            effectiveness = "Marginally effective - small blocking effect"
        else:
            effectiveness = "Not effective - consider using CRD instead"

        return {
            'total_variance': total_variance,
            'between_block_variance': between_block_var,
            'within_block_variance': within_block_var,
            'intraclass_correlation': icc,
            'effectiveness': effectiveness,
            'variance_explained_by_blocks': icc * 100
        }

    def get_design_summary(self) -> Dict:
        """
        Get summary of the current design.

        Returns:
            Dictionary containing design information
        """
        return self.design_info

    def export_design(
        self,
        file_path: str,
        format: str = 'csv'
    ) -> None:
        """
        Export the design matrix to a file.

        Args:
            file_path: Path to save the file
            format: File format ('csv' or 'excel')
        """
        if self.design_matrix is None:
            raise ValueError("No design has been created yet. Call create_design() first.")

        if format == 'csv':
            self.design_matrix.to_csv(file_path, index=False)
            logger.info(f"Design exported to {file_path}")
        elif format == 'excel':
            self.design_matrix.to_excel(file_path, index=False)
            logger.info(f"Design exported to {file_path}")
        else:
            raise ValueError(f"Unsupported format: {format}. Use 'csv' or 'excel'.")


def create_rbd_from_config(config: Dict) -> Tuple[pd.DataFrame, RandomizedBlockDesign]:
    """
    Create an RBD from a configuration dictionary.

    Args:
        config: Configuration dictionary containing:
            - data_path: Path to data file
            - treatments: List of treatment names
            - block_col: Name of blocking variable column
            - treatment_col: Name of treatment column (default: 'treatment')
            - replications: Number of reps per treatment per block (default: 1)
            - random_seed: Random seed (default: 42)

    Returns:
        Tuple of (design DataFrame, RBD object)

    Example:
        >>> config = {
        ...     'data_path': 'data/raw/ecommerce_data.csv',
        ...     'treatments': ['Control', 'Email_Only', 'SMS_Only', 'Both'],
        ...     'block_col': 'location',
        ...     'random_seed': 42
        ... }
        >>> design_df, rbd = create_rbd_from_config(config)
    """
    # Load data
    data = pd.read_csv(config['data_path'])

    # Create RBD object
    rbd = RandomizedBlockDesign(
        random_seed=config.get('random_seed', 42)
    )

    # Create design
    design_df = rbd.create_design(
        data=data,
        treatments=config['treatments'],
        block_col=config['block_col'],
        treatment_col=config.get('treatment_col', 'treatment'),
        replications=config.get('replications', 1)
    )

    return design_df, rbd


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create sample data with blocks
    np.random.seed(42)
    n_per_block = 40
    blocks = ['Location_A', 'Location_B', 'Location_C']

    sample_data = pd.DataFrame({
        'unit_id': range(n_per_block * len(blocks)),
        'location': np.repeat(blocks, n_per_block),
        'baseline_score': np.concatenate([
            np.random.randn(n_per_block) * 10 + 50,  # Location A
            np.random.randn(n_per_block) * 10 + 55,  # Location B (slightly higher)
            np.random.randn(n_per_block) * 10 + 48   # Location C (slightly lower)
        ])
    })

    # Create RBD
    rbd = RandomizedBlockDesign(random_seed=42)
    design = rbd.create_design(
        data=sample_data,
        treatments=['Control', 'Treatment_A', 'Treatment_B', 'Treatment_C'],
        block_col='location'
    )

    print("\nDesign Summary:")
    print(rbd.get_design_summary())

    print("\nTreatment distribution by block:")
    print(pd.crosstab(design['location'], design['treatment']))

    # Simulate response
    # Add treatment effects and block effects
    design['response'] = design['baseline_score'].copy()

    # Treatment effects
    design.loc[design['treatment'] == 'Treatment_A', 'response'] += 5
    design.loc[design['treatment'] == 'Treatment_B', 'response'] += 3

    # Add random error
    design['response'] += np.random.randn(len(design)) * 3

    # Analyze
    results = rbd.analyze_design(design, response_var='response', block_col='location')

    print("\nTwo-Way ANOVA Results:")
    print(f"Treatment Effect: F = {results['anova_table']['treatment']['f_statistic']:.4f}, "
          f"p = {results['anova_table']['treatment']['p_value']:.4f}")
    print(f"Block Effect: F = {results['anova_table']['block']['f_statistic']:.4f}, "
          f"p = {results['anova_table']['block']['p_value']:.4f}")
    print(f"\nRelative Efficiency vs CRD: {results['relative_efficiency']['vs_crd']:.2f} "
          f"({results['relative_efficiency']['percent_improvement']:.1f}% improvement)")

    # Check block effectiveness
    effectiveness = rbd.check_block_effectiveness(design, 'response', 'location')
    print(f"\nBlock Effectiveness:")
    print(f"ICC = {effectiveness['intraclass_correlation']:.4f}")
    print(f"{effectiveness['effectiveness']}")
