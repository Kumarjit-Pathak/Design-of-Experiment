"""
Balance Checker Module

This module checks the balance between treatment and control groups (or multiple groups)
on baseline covariates. It calculates standardized mean differences (Cohen's d),
performs statistical tests, and prepares data for Love plots.

This is CRITICAL for validating that treatment and control groups are comparable
before analyzing treatment effects.

Author: DOE Simulator Team
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.statistical_tests import (
    calculate_cohens_d,
    interpret_cohens_d,
    independent_ttest,
    chi_square_test
)


class BalanceChecker:
    """
    Class to check balance between treatment and control groups.

    Provides methods to:
    - Calculate standardized mean differences
    - Perform balance tests
    - Generate balance tables
    - Prepare Love plot data
    - Provide interpretation
    """

    def __init__(
        self,
        data: pd.DataFrame,
        treatment_col: str,
        group_labels: Optional[Dict[Any, str]] = None
    ):
        """
        Initialize BalanceChecker.

        Args:
            data: DataFrame containing treatment assignments and covariates
            treatment_col: Column name containing treatment assignments
            group_labels: Optional dict mapping treatment values to labels
                         e.g., {0: 'Control', 1: 'Treatment'}

        Example:
            >>> checker = BalanceChecker(df, treatment_col='treatment_group')
            >>> results = checker.check_balance(['age', 'gender', 'income'])
        """
        self.data = data.copy()
        self.treatment_col = treatment_col
        self.group_labels = group_labels or {}

        # Validate treatment column
        if treatment_col not in data.columns:
            raise ValueError(f"Treatment column '{treatment_col}' not found")

        self.groups = data[treatment_col].unique()
        self.n_groups = len(self.groups)

        print(f"[INFO] BalanceChecker initialized")
        print(f"       Treatment column: {treatment_col}")
        print(f"       Number of groups: {self.n_groups}")
        print(f"       Groups: {list(self.groups)}")
        for group in self.groups:
            n = (data[treatment_col] == group).sum()
            print(f"       - {self._get_group_label(group)}: n={n}")

    def _get_group_label(self, group_value: Any) -> str:
        """Get label for group value."""
        return self.group_labels.get(group_value, str(group_value))

    def check_balance(
        self,
        covariates: List[str],
        threshold_smd: float = 0.1,
        perform_tests: bool = True,
        alpha: float = 0.05
    ) -> Dict[str, Any]:
        """
        Check balance on specified covariates.

        Args:
            covariates: List of covariate column names to check
            threshold_smd: Threshold for standardized mean difference (default 0.1)
            perform_tests: Whether to perform statistical tests
            alpha: Significance level for tests

        Returns:
            Dictionary with balance results

        Example:
            >>> results = checker.check_balance(
            ...     covariates=['age', 'gender', 'income'],
            ...     threshold_smd=0.1
            ... )
        """
        print("\n" + "="*70)
        print("BALANCE CHECKING")
        print("="*70)

        results = {
            'covariates_checked': covariates,
            'n_groups': self.n_groups,
            'groups': list(self.groups),
            'sample_sizes': {},
            'balance_results': [],
            'overall_balance': None,
            'love_plot_data': None
        }

        # Get sample sizes
        for group in self.groups:
            group_label = self._get_group_label(group)
            n = (self.data[self.treatment_col] == group).sum()
            results['sample_sizes'][group_label] = n

        # Check each covariate
        for covariate in covariates:
            if covariate not in self.data.columns:
                print(f"[WARNING] Covariate '{covariate}' not found, skipping")
                continue

            covariate_result = self._check_covariate_balance(
                covariate,
                threshold_smd,
                perform_tests,
                alpha
            )

            results['balance_results'].append(covariate_result)

        # Calculate overall balance score
        results['overall_balance'] = self._calculate_overall_balance(
            results['balance_results'],
            threshold_smd
        )

        # Prepare Love plot data
        results['love_plot_data'] = self._prepare_love_plot_data(
            results['balance_results']
        )

        return results

    def _check_covariate_balance(
        self,
        covariate: str,
        threshold_smd: float,
        perform_tests: bool,
        alpha: float
    ) -> Dict[str, Any]:
        """Check balance for a single covariate."""
        result = {
            'covariate': covariate,
            'type': None,
            'balanced': False,
            'interpretation': None
        }

        # Determine variable type
        if pd.api.types.is_numeric_dtype(self.data[covariate]):
            result['type'] = 'numerical'
            balance_result = self._check_numerical_balance(
                covariate, threshold_smd, perform_tests, alpha
            )
        else:
            result['type'] = 'categorical'
            balance_result = self._check_categorical_balance(
                covariate, threshold_smd, perform_tests, alpha
            )

        result.update(balance_result)

        return result

    def _check_numerical_balance(
        self,
        covariate: str,
        threshold_smd: float,
        perform_tests: bool,
        alpha: float
    ) -> Dict[str, Any]:
        """Check balance for numerical covariate."""
        # For two groups, calculate standardized mean difference
        if self.n_groups == 2:
            group1_data = self.data[self.data[self.treatment_col] == self.groups[0]][covariate]
            group2_data = self.data[self.data[self.treatment_col] == self.groups[1]][covariate]

            # Calculate Cohen's d
            smd = calculate_cohens_d(group1_data, group2_data, pooled=True)

            # Group statistics
            stats = {
                f'{self._get_group_label(self.groups[0])}_mean': group1_data.mean(),
                f'{self._get_group_label(self.groups[1])}_mean': group2_data.mean(),
                f'{self._get_group_label(self.groups[0])}_std': group1_data.std(),
                f'{self._get_group_label(self.groups[1])}_std': group2_data.std(),
                'mean_difference': group1_data.mean() - group2_data.mean(),
                'standardized_mean_difference': smd,
                'abs_smd': abs(smd)
            }

            # Determine balance
            balanced = abs(smd) < threshold_smd

            # Interpretation
            if abs(smd) < 0.1:
                interpretation = "Excellent balance"
            elif abs(smd) < 0.2:
                interpretation = "Good balance"
            elif abs(smd) < 0.3:
                interpretation = "Acceptable balance"
            else:
                interpretation = "Poor balance - adjustment recommended"

            result = {
                **stats,
                'balanced': balanced,
                'interpretation': interpretation
            }

            # Statistical test
            if perform_tests:
                test_result = independent_ttest(group1_data, group2_data, alpha=alpha)
                result['test_statistic'] = test_result['t_statistic']
                result['p_value'] = test_result['p_value']
                result['significant'] = test_result['significant']
                result['ci_lower'] = test_result['ci_lower']
                result['ci_upper'] = test_result['ci_upper']

        else:
            # For multiple groups, calculate maximum pairwise SMD
            max_smd = 0
            group_means = {}

            for group in self.groups:
                group_label = self._get_group_label(group)
                group_data = self.data[self.data[self.treatment_col] == group][covariate]
                group_means[group_label] = group_data.mean()

            # Calculate pairwise SMDs
            for i, group1 in enumerate(self.groups):
                for group2 in self.groups[i+1:]:
                    g1_data = self.data[self.data[self.treatment_col] == group1][covariate]
                    g2_data = self.data[self.data[self.treatment_col] == group2][covariate]
                    smd = abs(calculate_cohens_d(g1_data, g2_data))
                    if smd > max_smd:
                        max_smd = smd

            result = {
                'group_means': group_means,
                'max_pairwise_smd': max_smd,
                'balanced': max_smd < threshold_smd,
                'interpretation': interpret_cohens_d(max_smd)
            }

        return result

    def _check_categorical_balance(
        self,
        covariate: str,
        threshold_smd: float,
        perform_tests: bool,
        alpha: float
    ) -> Dict[str, Any]:
        """Check balance for categorical covariate."""
        # Get proportions for each group
        distributions = {}

        for group in self.groups:
            group_label = self._get_group_label(group)
            group_data = self.data[self.data[self.treatment_col] == group][covariate]
            dist = group_data.value_counts(normalize=True).to_dict()
            distributions[group_label] = dist

        # For two groups, calculate chi-square test
        if self.n_groups == 2 and perform_tests:
            group1_data = self.data[self.data[self.treatment_col] == self.groups[0]][covariate]
            group2_data = self.data[self.data[self.treatment_col] == self.groups[1]][covariate]

            test_result = chi_square_test(group1_data, group2_data, alpha=alpha)

            # Calculate maximum absolute difference in proportions
            max_diff = 0
            for category in set(group1_data.unique()) | set(group2_data.unique()):
                prop1 = (group1_data == category).mean()
                prop2 = (group2_data == category).mean()
                diff = abs(prop1 - prop2)
                if diff > max_diff:
                    max_diff = diff

            result = {
                'distributions': distributions,
                'chi_square': test_result['chi2'],
                'p_value': test_result['p_value'],
                'significant': test_result['significant'],
                'cramers_v': test_result['cramers_v'],
                'max_proportion_diff': max_diff,
                'balanced': not test_result['significant'] and max_diff < 0.1,
                'interpretation': 'Balanced' if not test_result['significant'] else 'Imbalanced'
            }
        else:
            result = {
                'distributions': distributions,
                'balanced': True,  # Simplified for multiple groups
                'interpretation': 'Check distributions manually'
            }

        return result

    def _calculate_overall_balance(
        self,
        balance_results: List[Dict],
        threshold_smd: float
    ) -> Dict[str, Any]:
        """Calculate overall balance score."""
        n_covariates = len(balance_results)
        n_balanced = sum(1 for r in balance_results if r.get('balanced', False))

        balance_score = (n_balanced / n_covariates * 100) if n_covariates > 0 else 0

        # Traffic light system
        if balance_score >= 90:
            status = "EXCELLENT"
            color = "green"
        elif balance_score >= 70:
            status = "GOOD"
            color = "yellow"
        elif balance_score >= 50:
            status = "ACCEPTABLE"
            color = "orange"
        else:
            status = "POOR"
            color = "red"

        return {
            'n_covariates': n_covariates,
            'n_balanced': n_balanced,
            'balance_percentage': balance_score,
            'status': status,
            'color': color,
            'recommendation': self._get_balance_recommendation(balance_score)
        }

    def _get_balance_recommendation(self, balance_score: float) -> str:
        """Get recommendation based on balance score."""
        if balance_score >= 90:
            return "Groups are well-balanced. Proceed with analysis."
        elif balance_score >= 70:
            return "Groups show good balance. Consider reporting any imbalanced covariates."
        elif balance_score >= 50:
            return "Some imbalance detected. Consider covariate adjustment or propensity scores."
        else:
            return "Significant imbalance detected. Strongly recommend adjustment methods (ANCOVA, propensity scores, matching)."

    def _prepare_love_plot_data(
        self,
        balance_results: List[Dict]
    ) -> pd.DataFrame:
        """
        Prepare data for Love plot visualization.

        Love plot shows standardized mean differences for all covariates
        with reference lines at ±0.1, ±0.2, ±0.3
        """
        love_data = []

        for result in balance_results:
            if result['type'] == 'numerical':
                if 'standardized_mean_difference' in result:
                    smd = result['standardized_mean_difference']
                    abs_smd = abs(smd)

                    # Color coding
                    if abs_smd < 0.1:
                        color = 'green'
                        status = 'Excellent'
                    elif abs_smd < 0.2:
                        color = 'yellow'
                        status = 'Good'
                    elif abs_smd < 0.3:
                        color = 'orange'
                        status = 'Acceptable'
                    else:
                        color = 'red'
                        status = 'Poor'

                    love_data.append({
                        'covariate': result['covariate'],
                        'smd': smd,
                        'abs_smd': abs_smd,
                        'color': color,
                        'status': status,
                        'balanced': result['balanced']
                    })

        love_df = pd.DataFrame(love_data)

        # Sort by absolute SMD (descending) for better visualization
        if not love_df.empty:
            love_df = love_df.sort_values('abs_smd', ascending=False).reset_index(drop=True)

        return love_df

    def create_balance_table(
        self,
        balance_results: Dict[str, Any],
        format: str = 'markdown'
    ) -> str:
        """
        Create formatted balance table.

        Args:
            balance_results: Results from check_balance()
            format: 'markdown', 'html', or 'latex'

        Returns:
            Formatted table string
        """
        # Create DataFrame for display
        display_data = []

        for result in balance_results['balance_results']:
            if result['type'] == 'numerical':
                row = {
                    'Covariate': result['covariate'],
                    'Type': 'Numerical',
                    'SMD': f"{result.get('standardized_mean_difference', 0):.3f}",
                    '|SMD|': f"{result.get('abs_smd', 0):.3f}",
                    'Balanced': 'Yes' if result['balanced'] else 'No',
                    'Status': result['interpretation']
                }
            else:
                row = {
                    'Covariate': result['covariate'],
                    'Type': 'Categorical',
                    'SMD': 'N/A',
                    '|SMD|': 'N/A',
                    'Balanced': 'Yes' if result['balanced'] else 'No',
                    'Status': result.get('interpretation', 'Check distributions')
                }

            display_data.append(row)

        df = pd.DataFrame(display_data)

        if format == 'markdown':
            return df.to_markdown(index=False)
        elif format == 'html':
            return df.to_html(index=False)
        elif format == 'latex':
            return df.to_latex(index=False)
        else:
            return df.to_string(index=False)

    def print_balance_summary(self, balance_results: Dict[str, Any]) -> None:
        """Print comprehensive balance summary."""
        print("\n" + "="*70)
        print("BALANCE CHECK SUMMARY")
        print("="*70)

        # Sample sizes
        print("\nSample Sizes:")
        for group_label, n in balance_results['sample_sizes'].items():
            print(f"  {group_label}: n={n}")

        # Overall balance
        overall = balance_results['overall_balance']
        print(f"\nOverall Balance Score: {overall['balance_percentage']:.1f}%")
        print(f"Status: {overall['status']}")
        print(f"Balanced covariates: {overall['n_balanced']}/{overall['n_covariates']}")

        # Recommendation
        print(f"\nRecommendation:")
        print(f"  {overall['recommendation']}")

        # Detailed results
        print("\n" + "-"*70)
        print("Covariate-Level Results:")
        print("-"*70)

        for result in balance_results['balance_results']:
            print(f"\n{result['covariate']} ({result['type']}):")

            if result['type'] == 'numerical':
                if 'standardized_mean_difference' in result:
                    print(f"  SMD: {result['standardized_mean_difference']:.4f}")
                    print(f"  |SMD|: {result['abs_smd']:.4f}")
                    print(f"  Status: {result['interpretation']}")
                    print(f"  Balanced: {'Yes' if result['balanced'] else 'No'}")

                    if 'p_value' in result:
                        print(f"  t-test p-value: {result['p_value']:.4f}")

            else:  # Categorical
                print(f"  Status: {result['interpretation']}")
                print(f"  Balanced: {'Yes' if result['balanced'] else 'No'}")

                if 'p_value' in result:
                    print(f"  Chi-square p-value: {result['p_value']:.4f}")

        print("\n" + "="*70)


def run_balance_check(
    data: pd.DataFrame,
    treatment_col: str,
    covariates: List[str],
    threshold_smd: float = 0.1,
    group_labels: Optional[Dict] = None
) -> Dict[str, Any]:
    """
    Convenience function to run balance check.

    Args:
        data: DataFrame with treatment and covariates
        treatment_col: Name of treatment column
        covariates: List of covariates to check
        threshold_smd: SMD threshold for balance (default 0.1)
        group_labels: Optional group labels

    Returns:
        Balance check results dictionary

    Example:
        >>> results = run_balance_check(
        ...     df,
        ...     treatment_col='treatment',
        ...     covariates=['age', 'gender', 'income'],
        ...     group_labels={0: 'Control', 1: 'Treatment'}
        ... )
    """
    checker = BalanceChecker(data, treatment_col, group_labels)
    results = checker.check_balance(covariates, threshold_smd=threshold_smd)
    checker.print_balance_summary(results)

    return results


# Example usage
if __name__ == "__main__":
    # Example with mock data
    print("Balance Checker Example")
    print("="*70)

    # Create sample data with treatment assignment
    np.random.seed(42)
    n = 1000

    data = pd.DataFrame({
        'treatment': np.random.choice([0, 1], size=n),
        'age': np.random.normal(40, 10, n),
        'income': np.random.normal(50000, 15000, n),
        'gender': np.random.choice(['Male', 'Female'], n),
        'education': np.random.choice(['High School', 'Bachelor', 'Master'], n)
    })

    # Add slight imbalance
    data.loc[data['treatment'] == 1, 'age'] += 2

    # Run balance check
    results = run_balance_check(
        data,
        treatment_col='treatment',
        covariates=['age', 'income', 'gender', 'education'],
        group_labels={0: 'Control', 1: 'Treatment'}
    )

    # Display Love plot data
    print("\nLove Plot Data:")
    print(results['love_plot_data'].to_string(index=False))
