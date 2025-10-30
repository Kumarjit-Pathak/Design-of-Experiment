"""
Factorial Design

A factorial design investigates the effects of multiple factors simultaneously,
including main effects and interactions. A full k-factor design with each factor
at 2 levels requires 2^k experimental runs.

Key Features:
- Studies multiple factors simultaneously
- Detects interactions between factors
- More efficient than one-factor-at-a-time (OFAT) experiments
- Provides complete picture of factor effects

Mathematical Model (2-factor example):
    Y_ijk = μ + α_i + β_j + (αβ)_ij + ε_ijk

Where:
    Y_ijk = kth observation at level i of factor A and level j of factor B
    μ = overall mean
    α_i = main effect of factor A at level i
    β_j = main effect of factor B at level j
    (αβ)_ij = interaction effect between factors A and B
    ε_ijk = random error

Advantages:
- Efficient: tests multiple factors in fewer runs than OFAT
- Detects interactions (synergistic/antagonistic effects)
- Provides more information per experimental run

Types Supported:
- 2^k designs (all factors at 2 levels)
- 3^k designs (all factors at 3 levels)
- Mixed-level designs (factors at different numbers of levels)

Author: DOE Simulator Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Union, Optional, Tuple
from itertools import product
import logging
from scipy import stats

logger = logging.getLogger(__name__)


class FactorialDesign:
    """
    Full Factorial Design implementation.

    Supports:
    - 2^k factorial designs (most common)
    - Multi-level factorial designs
    - Main effects and interaction analysis
    - Effect size calculations
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize Factorial Design generator.

        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        np.random.seed(random_seed)
        self.design_matrix = None
        self.design_info = {}
        self.factors = {}

    def create_design(
        self,
        factors: Dict[str, List],
        replications: int = 1,
        randomize: bool = True
    ) -> pd.DataFrame:
        """
        Create a full factorial design matrix.

        Args:
            factors: Dictionary mapping factor names to their levels
                    Example: {'Temperature': [20, 30, 40],
                             'Pressure': [1, 2],
                             'Catalyst': ['A', 'B']}
            replications: Number of replications for each treatment combination
            randomize: Whether to randomize the run order

        Returns:
            DataFrame containing the design matrix with all factor combinations

        Example:
            >>> factorial = FactorialDesign(random_seed=42)
            >>> factors = {
            ...     'Email_Campaign': ['No', 'Yes'],
            ...     'SMS_Campaign': ['No', 'Yes'],
            ...     'Discount': [0, 10, 20]
            ... }
            >>> design = factorial.create_design(factors, replications=2)
        """
        if not factors:
            raise ValueError("Must specify at least one factor")

        # Store factor information
        self.factors = factors
        factor_names = list(factors.keys())
        n_factors = len(factor_names)

        # Generate all combinations (Cartesian product)
        factor_combinations = list(product(*factors.values()))
        n_combinations = len(factor_combinations)

        logger.info(f"Creating factorial design with {n_factors} factors:")
        for name, levels in factors.items():
            logger.info(f"  {name}: {len(levels)} levels = {levels}")
        logger.info(f"Total treatment combinations: {n_combinations}")
        logger.info(f"Replications: {replications}")
        logger.info(f"Total runs: {n_combinations * replications}")

        # Create design matrix
        design_rows = []
        for rep in range(replications):
            for combo in factor_combinations:
                row = {factor_names[i]: combo[i] for i in range(n_factors)}
                row['replication'] = rep + 1
                design_rows.append(row)

        design_df = pd.DataFrame(design_rows)

        # Add run order
        design_df['std_order'] = range(1, len(design_df) + 1)

        # Randomize if requested
        if randomize:
            design_df['run_order'] = np.random.permutation(len(design_df)) + 1
            design_df = design_df.sort_values('run_order').reset_index(drop=True)
        else:
            design_df['run_order'] = design_df['std_order']

        # Store design information
        self.design_matrix = design_df
        self.design_info = {
            'design_type': 'Full Factorial Design',
            'n_factors': n_factors,
            'factors': factors,
            'factor_names': factor_names,
            'n_levels': [len(levels) for levels in factors.values()],
            'n_combinations': n_combinations,
            'replications': replications,
            'total_runs': len(design_df),
            'randomized': randomize,
            'random_seed': self.random_seed
        }

        return design_df

    def assign_to_units(
        self,
        design_df: pd.DataFrame,
        data: pd.DataFrame,
        unit_id_col: str = 'unit_id'
    ) -> pd.DataFrame:
        """
        Assign the factorial design to experimental units from a dataset.

        Args:
            design_df: Design matrix from create_design()
            data: DataFrame containing experimental units
            unit_id_col: Name of unit identifier column

        Returns:
            DataFrame with design assignments mapped to actual units

        Example:
            >>> assigned = factorial.assign_to_units(design, customer_data)
        """
        n_runs = len(design_df)
        n_units = len(data)

        if n_units < n_runs:
            raise ValueError(
                f"Not enough experimental units ({n_units}) for design runs ({n_runs})"
            )

        # Randomly sample units
        selected_units = data.sample(n=n_runs, random_state=self.random_seed)

        # Merge design with units
        result_df = pd.concat([
            selected_units.reset_index(drop=True),
            design_df.reset_index(drop=True)
        ], axis=1)

        logger.info(f"Assigned {n_runs} design runs to {n_runs} experimental units")

        return result_df

    def analyze_effects(
        self,
        design_df: pd.DataFrame,
        response_var: str,
        include_interactions: bool = True,
        max_interaction_order: int = 2
    ) -> Dict:
        """
        Analyze main effects and interactions in factorial design.

        Performs multi-way ANOVA to assess:
        - Main effects of each factor
        - Two-way interactions (if include_interactions=True)
        - Higher-order interactions (up to max_interaction_order)

        Args:
            design_df: DataFrame with factor assignments and response
            response_var: Name of the response variable
            include_interactions: Whether to analyze interaction effects
            max_interaction_order: Maximum order of interactions (2, 3, etc.)

        Returns:
            Dictionary containing effects analysis results

        Example:
            >>> results = factorial.analyze_effects(
            ...     design_df,
            ...     response_var='conversion_rate',
            ...     include_interactions=True
            ... )
        """
        if response_var not in design_df.columns:
            raise ValueError(f"Response variable '{response_var}' not found")

        factor_names = self.design_info['factor_names']
        analysis_df = design_df[factor_names + [response_var]].dropna()

        # Calculate grand mean
        grand_mean = analysis_df[response_var].mean()
        n = len(analysis_df)

        results = {
            'design_type': 'Factorial',
            'response_variable': response_var,
            'n_observations': n,
            'grand_mean': grand_mean,
            'main_effects': {},
            'interactions': {}
        }

        # Analyze main effects
        for factor in factor_names:
            factor_means = analysis_df.groupby(factor)[response_var].mean()
            factor_counts = analysis_df.groupby(factor)[response_var].count()

            # Calculate SS for this factor
            ss_factor = sum(
                factor_counts[level] * (factor_means[level] - grand_mean) ** 2
                for level in factor_means.index
            )

            # F-test (one-way ANOVA)
            groups = [
                analysis_df[analysis_df[factor] == level][response_var].values
                for level in factor_means.index
            ]
            f_stat, p_value = stats.f_oneway(*groups)

            # Effect size
            ss_total = ((analysis_df[response_var] - grand_mean) ** 2).sum()
            eta_squared = ss_factor / ss_total if ss_total > 0 else 0

            results['main_effects'][factor] = {
                'levels': list(factor_means.index),
                'means': factor_means.to_dict(),
                'f_statistic': f_stat,
                'p_value': p_value,
                'significant': p_value < 0.05,
                'eta_squared': eta_squared,
                'interpretation': self._interpret_effect_size(eta_squared)
            }

            logger.info(f"Main effect of {factor}: F = {f_stat:.4f}, p = {p_value:.4f}, η² = {eta_squared:.4f}")

        # Analyze interactions
        if include_interactions and len(factor_names) >= 2:
            # Two-way interactions
            from itertools import combinations

            for factor_a, factor_b in combinations(factor_names, 2):
                interaction_result = self._analyze_interaction(
                    analysis_df, response_var, factor_a, factor_b, grand_mean
                )
                interaction_name = f"{factor_a} × {factor_b}"
                results['interactions'][interaction_name] = interaction_result

                logger.info(
                    f"Interaction {interaction_name}: "
                    f"F = {interaction_result['f_statistic']:.4f}, "
                    f"p = {interaction_result['p_value']:.4f}"
                )

            # Three-way interactions (if requested)
            if max_interaction_order >= 3 and len(factor_names) >= 3:
                for factor_a, factor_b, factor_c in combinations(factor_names, 3):
                    interaction_result = self._analyze_three_way_interaction(
                        analysis_df, response_var, factor_a, factor_b, factor_c
                    )
                    interaction_name = f"{factor_a} × {factor_b} × {factor_c}"
                    results['interactions'][interaction_name] = interaction_result

        return results

    def _analyze_interaction(
        self,
        df: pd.DataFrame,
        response_var: str,
        factor_a: str,
        factor_b: str,
        grand_mean: float
    ) -> Dict:
        """
        Analyze two-way interaction between factors.

        Args:
            df: Data with factors and response
            response_var: Response variable name
            factor_a: First factor name
            factor_b: Second factor name
            grand_mean: Grand mean of response

        Returns:
            Dictionary with interaction analysis results
        """
        # Group by both factors
        interaction_means = df.groupby([factor_a, factor_b])[response_var].mean()
        interaction_counts = df.groupby([factor_a, factor_b])[response_var].count()

        # Main effect means
        mean_a = df.groupby(factor_a)[response_var].mean()
        mean_b = df.groupby(factor_b)[response_var].mean()

        # Calculate interaction SS
        ss_interaction = 0
        for (level_a, level_b), cell_mean in interaction_means.items():
            expected = mean_a[level_a] + mean_b[level_b] - grand_mean
            n_cell = interaction_counts[(level_a, level_b)]
            ss_interaction += n_cell * (cell_mean - expected) ** 2

        # Approximate F-test using two-way ANOVA
        # Group data by combination
        groups = []
        for level_a in df[factor_a].unique():
            for level_b in df[factor_b].unique():
                group_data = df[
                    (df[factor_a] == level_a) & (df[factor_b] == level_b)
                ][response_var].values
                if len(group_data) > 0:
                    groups.append(group_data)

        if len(groups) > 1:
            f_stat, p_value = stats.f_oneway(*groups)
        else:
            f_stat, p_value = 0, 1.0

        ss_total = ((df[response_var] - grand_mean) ** 2).sum()
        eta_squared = ss_interaction / ss_total if ss_total > 0 else 0

        return {
            'factors': [factor_a, factor_b],
            'cell_means': interaction_means.to_dict(),
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05,
            'eta_squared': eta_squared,
            'interpretation': self._interpret_effect_size(eta_squared)
        }

    def _analyze_three_way_interaction(
        self,
        df: pd.DataFrame,
        response_var: str,
        factor_a: str,
        factor_b: str,
        factor_c: str
    ) -> Dict:
        """
        Analyze three-way interaction (simplified).

        Args:
            df: Data with factors and response
            response_var: Response variable name
            factor_a, factor_b, factor_c: Factor names

        Returns:
            Dictionary with three-way interaction results
        """
        # Group by all three factors
        interaction_means = df.groupby([factor_a, factor_b, factor_c])[response_var].mean()

        # Simplified F-test
        groups = []
        for level_a in df[factor_a].unique():
            for level_b in df[factor_b].unique():
                for level_c in df[factor_c].unique():
                    group_data = df[
                        (df[factor_a] == level_a) &
                        (df[factor_b] == level_b) &
                        (df[factor_c] == level_c)
                    ][response_var].values
                    if len(group_data) > 0:
                        groups.append(group_data)

        if len(groups) > 1:
            f_stat, p_value = stats.f_oneway(*groups)
        else:
            f_stat, p_value = 0, 1.0

        return {
            'factors': [factor_a, factor_b, factor_c],
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant': p_value < 0.05
        }

    def _interpret_effect_size(self, eta_squared: float) -> str:
        """Interpret eta-squared effect size."""
        if eta_squared < 0.01:
            return "negligible"
        elif eta_squared < 0.06:
            return "small"
        elif eta_squared < 0.14:
            return "medium"
        else:
            return "large"

    def create_interaction_plot_data(
        self,
        design_df: pd.DataFrame,
        response_var: str,
        factor_a: str,
        factor_b: str
    ) -> pd.DataFrame:
        """
        Prepare data for interaction plot (line plot showing how effect of one
        factor changes across levels of another factor).

        Args:
            design_df: DataFrame with factors and response
            response_var: Response variable
            factor_a: Factor for x-axis
            factor_b: Factor for separate lines

        Returns:
            DataFrame with aggregated means for plotting
        """
        plot_data = design_df.groupby([factor_a, factor_b])[response_var].agg(['mean', 'sem']).reset_index()
        plot_data.columns = [factor_a, factor_b, 'mean', 'sem']

        return plot_data

    def get_design_summary(self) -> Dict:
        """Get summary of the design."""
        return self.design_info

    def export_design(self, file_path: str, format: str = 'csv') -> None:
        """Export design matrix to file."""
        if self.design_matrix is None:
            raise ValueError("No design created yet")

        if format == 'csv':
            self.design_matrix.to_csv(file_path, index=False)
        elif format == 'excel':
            self.design_matrix.to_excel(file_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        logger.info(f"Design exported to {file_path}")


if __name__ == "__main__":
    # Example: 2^3 factorial design for e-commerce marketing
    logging.basicConfig(level=logging.INFO)

    factorial = FactorialDesign(random_seed=42)

    # Define factors (2 levels each = 2^3 = 8 treatment combinations)
    factors = {
        'Email_Campaign': ['No', 'Yes'],
        'SMS_Campaign': ['No', 'Yes'],
        'Discount': ['0%', '10%']
    }

    # Create design
    design = factorial.create_design(factors, replications=3, randomize=True)

    print("\nFactorial Design Matrix:")
    print(design)

    print("\nDesign Summary:")
    summary = factorial.get_design_summary()
    for key, value in summary.items():
        print(f"{key}: {value}")

    # Simulate response (with interaction between Email and Discount)
    design['conversion_rate'] = 10  # Baseline

    # Main effects
    design.loc[design['Email_Campaign'] == 'Yes', 'conversion_rate'] += 5
    design.loc[design['SMS_Campaign'] == 'Yes', 'conversion_rate'] += 2
    design.loc[design['Discount'] == '10%', 'conversion_rate'] += 3

    # Interaction: Email + Discount has synergistic effect
    design.loc[
        (design['Email_Campaign'] == 'Yes') & (design['Discount'] == '10%'),
        'conversion_rate'
    ] += 4  # Extra boost!

    # Add random noise
    design['conversion_rate'] += np.random.randn(len(design)) * 1.5

    # Analyze effects
    results = factorial.analyze_effects(design, response_var='conversion_rate')

    print("\n=== Main Effects ===")
    for factor, effect in results['main_effects'].items():
        print(f"\n{factor}:")
        print(f"  F-statistic: {effect['f_statistic']:.4f}")
        print(f"  P-value: {effect['p_value']:.4f}")
        print(f"  Effect size: {effect['eta_squared']:.4f} ({effect['interpretation']})")
        print(f"  Means by level: {effect['means']}")

    print("\n=== Interaction Effects ===")
    for interaction, effect in results['interactions'].items():
        print(f"\n{interaction}:")
        print(f"  F-statistic: {effect['f_statistic']:.4f}")
        print(f"  P-value: {effect['p_value']:.4f}")
        print(f"  Effect size: {effect['eta_squared']:.4f}")
