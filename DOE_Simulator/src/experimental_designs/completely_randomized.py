"""
Completely Randomized Design (CRD)

The simplest experimental design where treatments are assigned to experimental
units completely at random. This design is most appropriate when:
- Experimental units are homogeneous
- Environmental conditions are uniform
- No known sources of variation to block

CRD maximizes degrees of freedom for error estimation but requires homogeneous
experimental units for validity.

Mathematical Model:
    Y_ij = μ + τ_i + ε_ij

Where:
    Y_ij = jth observation receiving treatment i
    μ = overall mean
    τ_i = effect of treatment i
    ε_ij = random error (assumed N(0, σ²))

Author: DOE Simulator Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class CompletelyRandomizedDesign:
    """
    Completely Randomized Design (CRD) implementation.

    This class handles:
    - Random treatment assignment
    - Balance checking across treatments
    - Design matrix generation
    - ANOVA analysis
    - Effect size calculations
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize CRD designer.

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
        treatment_col: str = 'treatment',
        sample_sizes: Optional[Dict[str, int]] = None,
        balance_check: bool = True
    ) -> pd.DataFrame:
        """
        Create a completely randomized design by assigning treatments to units.

        Args:
            data: DataFrame containing experimental units
            treatments: List of treatment names/labels
            treatment_col: Name of the column to store treatment assignment
            sample_sizes: Dict mapping treatment names to sample sizes.
                         If None, uses equal allocation.
            balance_check: Whether to check balance on baseline covariates

        Returns:
            DataFrame with treatment assignments added

        Raises:
            ValueError: If sample sizes exceed available data

        Example:
            >>> crd = CompletelyRandomizedDesign(random_seed=42)
            >>> data = pd.DataFrame({'unit_id': range(100), 'baseline': np.random.randn(100)})
            >>> treatments = ['Control', 'Treatment_A', 'Treatment_B']
            >>> design = crd.create_design(data, treatments)
        """
        n_units = len(data)
        n_treatments = len(treatments)

        # Validate inputs
        if n_treatments == 0:
            raise ValueError("Must specify at least one treatment")

        # Determine sample sizes
        if sample_sizes is None:
            # Equal allocation
            base_size = n_units // n_treatments
            remainder = n_units % n_treatments
            sample_sizes = {
                t: base_size + (1 if i < remainder else 0)
                for i, t in enumerate(treatments)
            }
        else:
            # Validate custom sample sizes
            total_requested = sum(sample_sizes.values())
            if total_requested > n_units:
                raise ValueError(
                    f"Total sample size ({total_requested}) exceeds available units ({n_units})"
                )
            if total_requested < n_units:
                logger.warning(
                    f"Sample sizes sum to {total_requested}, but {n_units} units available. "
                    f"{n_units - total_requested} units will not be assigned."
                )

        # Create treatment assignment vector
        treatment_assignment = []
        for treatment, size in sample_sizes.items():
            treatment_assignment.extend([treatment] * size)

        # Fill remaining slots with None if any
        remaining = n_units - len(treatment_assignment)
        if remaining > 0:
            treatment_assignment.extend([None] * remaining)

        # Randomize assignment
        np.random.shuffle(treatment_assignment)

        # Assign to dataframe
        design_df = data.copy()
        design_df[treatment_col] = treatment_assignment

        # Store design information
        self.design_matrix = design_df
        self.design_info = {
            'design_type': 'Completely Randomized Design (CRD)',
            'n_units': n_units,
            'n_treatments': n_treatments,
            'treatments': treatments,
            'sample_sizes': sample_sizes,
            'treatment_col': treatment_col,
            'random_seed': self.random_seed,
            'balance_checked': balance_check
        }

        # Log design summary
        logger.info(f"CRD created with {n_treatments} treatments and {n_units} units")
        for treatment, size in sample_sizes.items():
            logger.info(f"  {treatment}: n={size} ({size/n_units*100:.1f}%)")

        # Perform balance check if requested
        if balance_check:
            self._check_balance(design_df, treatment_col, treatments)

        return design_df

    def _check_balance(
        self,
        design_df: pd.DataFrame,
        treatment_col: str,
        treatments: List[str]
    ) -> Dict:
        """
        Check balance of baseline covariates across treatment groups.

        Args:
            design_df: DataFrame with treatment assignments
            treatment_col: Name of treatment column
            treatments: List of treatment names

        Returns:
            Dictionary containing balance check results
        """
        # Identify baseline covariates (exclude treatment and identifiers)
        exclude_cols = [treatment_col, 'customer_id', 'unit_id', 'id']
        potential_covariates = [
            col for col in design_df.columns
            if col not in exclude_cols and design_df[col].dtype in ['float64', 'int64', 'object']
        ]

        balance_results = {}

        for covariate in potential_covariates[:10]:  # Check first 10 to avoid overload
            try:
                if design_df[covariate].dtype == 'object':
                    # Categorical: use chi-square test
                    contingency_table = pd.crosstab(
                        design_df[treatment_col],
                        design_df[covariate]
                    )
                    chi2, p_value, _, _ = stats.chi2_contingency(contingency_table)
                    balance_results[covariate] = {
                        'type': 'categorical',
                        'test': 'chi-square',
                        'statistic': chi2,
                        'p_value': p_value,
                        'balanced': p_value > 0.05
                    }
                else:
                    # Numerical: use ANOVA
                    groups = [
                        design_df[design_df[treatment_col] == t][covariate].dropna()
                        for t in treatments
                    ]
                    f_stat, p_value = stats.f_oneway(*groups)
                    balance_results[covariate] = {
                        'type': 'numerical',
                        'test': 'ANOVA',
                        'statistic': f_stat,
                        'p_value': p_value,
                        'balanced': p_value > 0.05
                    }
            except Exception as e:
                logger.warning(f"Could not check balance for {covariate}: {e}")
                continue

        self.design_info['balance_results'] = balance_results

        # Summary
        n_balanced = sum(1 for r in balance_results.values() if r['balanced'])
        n_total = len(balance_results)
        logger.info(f"Balance check: {n_balanced}/{n_total} covariates balanced (p > 0.05)")

        return balance_results

    def analyze_design(
        self,
        design_df: pd.DataFrame,
        response_var: str,
        treatment_col: str = 'treatment'
    ) -> Dict:
        """
        Perform ANOVA analysis on the experimental results.

        Args:
            design_df: DataFrame with treatment assignments and response
            response_var: Name of the response variable column
            treatment_col: Name of the treatment column

        Returns:
            Dictionary containing ANOVA results and effect sizes

        Example:
            >>> results = crd.analyze_design(design_df, response_var='yield')
        """
        # Remove missing values
        analysis_df = design_df[[treatment_col, response_var]].dropna()

        # Get unique treatments
        treatments = analysis_df[treatment_col].unique()

        # Prepare groups for ANOVA
        groups = [
            analysis_df[analysis_df[treatment_col] == t][response_var].values
            for t in treatments
        ]

        # One-way ANOVA
        f_stat, p_value = stats.f_oneway(*groups)

        # Calculate means and standard deviations
        treatment_stats = {}
        for treatment in treatments:
            group_data = analysis_df[analysis_df[treatment_col] == treatment][response_var]
            treatment_stats[treatment] = {
                'mean': group_data.mean(),
                'std': group_data.std(),
                'n': len(group_data),
                'se': group_data.sem()
            }

        # Calculate effect size (eta-squared)
        grand_mean = analysis_df[response_var].mean()

        # Sum of squares between groups
        ss_between = sum(
            stats['n'] * (stats['mean'] - grand_mean)**2
            for stats in treatment_stats.values()
        )

        # Sum of squares total
        ss_total = ((analysis_df[response_var] - grand_mean)**2).sum()

        eta_squared = ss_between / ss_total if ss_total > 0 else 0

        # Interpret effect size
        if eta_squared < 0.01:
            effect_interpretation = "negligible"
        elif eta_squared < 0.06:
            effect_interpretation = "small"
        elif eta_squared < 0.14:
            effect_interpretation = "medium"
        else:
            effect_interpretation = "large"

        results = {
            'design_type': 'CRD',
            'response_variable': response_var,
            'n_treatments': len(treatments),
            'n_observations': len(analysis_df),
            'anova': {
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            },
            'effect_size': {
                'eta_squared': eta_squared,
                'interpretation': effect_interpretation
            },
            'treatment_statistics': treatment_stats
        }

        logger.info(f"ANOVA F({len(treatments)-1}, {len(analysis_df)-len(treatments)}) = {f_stat:.4f}, p = {p_value:.4f}")
        logger.info(f"Effect size (η²) = {eta_squared:.4f} ({effect_interpretation})")

        return results

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


def create_crd_from_config(config: Dict) -> Tuple[pd.DataFrame, CompletelyRandomizedDesign]:
    """
    Create a CRD from a configuration dictionary.

    Args:
        config: Configuration dictionary containing:
            - data_path: Path to data file
            - treatments: List of treatment names
            - treatment_col: Name of treatment column (default: 'treatment')
            - sample_sizes: Optional dict of treatment -> sample size
            - random_seed: Random seed (default: 42)
            - balance_check: Whether to check balance (default: True)

    Returns:
        Tuple of (design DataFrame, CRD object)

    Example:
        >>> config = {
        ...     'data_path': 'data/raw/ecommerce_data.csv',
        ...     'treatments': ['Control', 'Email', 'SMS', 'Both'],
        ...     'sample_sizes': {'Control': 250, 'Email': 250, 'SMS': 250, 'Both': 250},
        ...     'random_seed': 42
        ... }
        >>> design_df, crd = create_crd_from_config(config)
    """
    # Load data
    data = pd.read_csv(config['data_path'])

    # Create CRD object
    crd = CompletelyRandomizedDesign(
        random_seed=config.get('random_seed', 42)
    )

    # Create design
    design_df = crd.create_design(
        data=data,
        treatments=config['treatments'],
        treatment_col=config.get('treatment_col', 'treatment'),
        sample_sizes=config.get('sample_sizes'),
        balance_check=config.get('balance_check', True)
    )

    return design_df, crd


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create sample data
    np.random.seed(42)
    sample_data = pd.DataFrame({
        'unit_id': range(100),
        'baseline_score': np.random.randn(100) * 10 + 50,
        'age': np.random.randint(18, 75, 100),
        'gender': np.random.choice(['Male', 'Female'], 100)
    })

    # Create CRD
    crd = CompletelyRandomizedDesign(random_seed=42)
    design = crd.create_design(
        data=sample_data,
        treatments=['Control', 'Treatment_A', 'Treatment_B', 'Treatment_C']
    )

    print("\nDesign Summary:")
    print(crd.get_design_summary())

    print("\nFirst 10 assignments:")
    print(design[['unit_id', 'treatment', 'baseline_score']].head(10))

    # Simulate response and analyze
    design['response'] = design['baseline_score'] + np.where(
        design['treatment'] == 'Treatment_A', 5, 0
    ) + np.random.randn(len(design)) * 3

    results = crd.analyze_design(design, response_var='response')
    print("\nANOVA Results:")
    print(f"F-statistic: {results['anova']['f_statistic']:.4f}")
    print(f"P-value: {results['anova']['p_value']:.4f}")
    print(f"Effect size (η²): {results['effect_size']['eta_squared']:.4f}")
