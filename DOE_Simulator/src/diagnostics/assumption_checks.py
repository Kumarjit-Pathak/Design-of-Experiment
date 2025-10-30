"""
ANOVA Assumption Checking Module

ANOVA (Analysis of Variance) relies on three critical assumptions:
1. **Normality:** Residuals are normally distributed
2. **Homoscedasticity:** Equal variance across groups (homogeneity of variance)
3. **Independence:** Observations are independent

Violating these assumptions can lead to:
- Incorrect p-values
- Invalid confidence intervals
- Wrong conclusions about treatment effects

This module provides:
- Statistical tests for each assumption
- Visual diagnostics (Q-Q plots, residual plots)
- Interpretation and recommendations
- Transformation suggestions when assumptions fail

Author: DOE Simulator Team
Date: 2025
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class AssumptionChecker:
    """
    Check ANOVA assumptions: normality, homoscedasticity, and independence.

    Provides both statistical tests and visual diagnostic data for plotting.
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize assumption checker.

        Args:
            alpha: Significance level for hypothesis tests (default: 0.05)
        """
        self.alpha = alpha

    def check_normality(
        self,
        residuals: np.ndarray,
        method: str = 'shapiro'
    ) -> Dict:
        """
        Test if residuals are normally distributed.

        Args:
            residuals: Array of residuals from fitted model
            method: Test to use ('shapiro', 'anderson', 'ks', or 'all')

        Returns:
            Dictionary with test results and interpretation

        Example:
            >>> checker = AssumptionChecker()
            >>> residuals = np.random.randn(100)
            >>> result = checker.check_normality(residuals)
        """
        results = {}
        residuals_clean = residuals[~np.isnan(residuals)]

        if len(residuals_clean) < 3:
            return {
                'error': 'Insufficient data for normality testing',
                'n': len(residuals_clean)
            }

        # Shapiro-Wilk Test
        if method in ['shapiro', 'all']:
            if len(residuals_clean) <= 5000:
                statistic, p_value = stats.shapiro(residuals_clean)
                results['shapiro_wilk'] = {
                    'test_name': 'Shapiro-Wilk Test',
                    'statistic': statistic,
                    'p_value': p_value,
                    'significant': p_value < self.alpha,
                    'interpretation': self._interpret_normality_test(p_value, 'shapiro')
                }
            else:
                results['shapiro_wilk'] = {
                    'note': 'Sample too large for Shapiro-Wilk (n > 5000), use other tests'
                }

        # Anderson-Darling Test
        if method in ['anderson', 'all']:
            result = stats.anderson(residuals_clean, dist='norm')
            critical_value_5pct = result.critical_values[2]  # 5% significance level
            results['anderson_darling'] = {
                'test_name': 'Anderson-Darling Test',
                'statistic': result.statistic,
                'critical_value_5pct': critical_value_5pct,
                'significant': result.statistic > critical_value_5pct,
                'interpretation': 'Reject normality' if result.statistic > critical_value_5pct else 'Fail to reject normality'
            }

        # Kolmogorov-Smirnov Test
        if method in ['ks', 'all']:
            # Standardize residuals
            residuals_std = (residuals_clean - np.mean(residuals_clean)) / np.std(residuals_clean)
            statistic, p_value = stats.kstest(residuals_std, 'norm')
            results['kolmogorov_smirnov'] = {
                'test_name': 'Kolmogorov-Smirnov Test',
                'statistic': statistic,
                'p_value': p_value,
                'significant': p_value < self.alpha,
                'interpretation': self._interpret_normality_test(p_value, 'ks')
            }

        # Descriptive statistics
        results['descriptive'] = {
            'mean': np.mean(residuals_clean),
            'std': np.std(residuals_clean),
            'skewness': stats.skew(residuals_clean),
            'kurtosis': stats.kurtosis(residuals_clean),
            'n': len(residuals_clean)
        }

        # Overall assessment
        violations = sum(
            1 for test in results.values()
            if isinstance(test, dict) and test.get('significant', False)
        )

        if violations == 0:
            overall = "✅ Normality assumption appears satisfied"
        elif violations == 1:
            overall = "⚠️ Mild deviation from normality detected (consider transformation)"
        else:
            overall = "❌ Significant deviation from normality (transformation recommended)"

        results['overall_assessment'] = overall
        results['recommendation'] = self._normality_recommendation(results)

        logger.info(f"Normality check: {overall}")

        return results

    def check_homoscedasticity(
        self,
        data: pd.DataFrame,
        group_col: str,
        value_col: str,
        method: str = 'levene'
    ) -> Dict:
        """
        Test for equal variances across groups (homoscedasticity).

        Args:
            data: DataFrame with groups and values
            group_col: Column name for group labels
            value_col: Column name for values
            method: Test to use ('levene', 'bartlett', 'fligner', or 'all')

        Returns:
            Dictionary with test results and interpretation

        Example:
            >>> result = checker.check_homoscedasticity(df, 'treatment', 'response')
        """
        results = {}

        # Get groups
        groups = data[group_col].unique()
        group_data = [data[data[group_col] == g][value_col].dropna() for g in groups]

        # Filter out empty groups
        group_data = [g for g in group_data if len(g) > 0]

        if len(group_data) < 2:
            return {
                'error': 'Need at least 2 groups for homoscedasticity testing',
                'n_groups': len(group_data)
            }

        # Levene's Test (robust to non-normality)
        if method in ['levene', 'all']:
            statistic, p_value = stats.levene(*group_data, center='median')
            results['levene'] = {
                'test_name': "Levene's Test (robust)",
                'statistic': statistic,
                'p_value': p_value,
                'significant': p_value < self.alpha,
                'interpretation': 'Unequal variances' if p_value < self.alpha else 'Equal variances'
            }

        # Bartlett's Test (sensitive to non-normality)
        if method in ['bartlett', 'all']:
            statistic, p_value = stats.bartlett(*group_data)
            results['bartlett'] = {
                'test_name': "Bartlett's Test (assumes normality)",
                'statistic': statistic,
                'p_value': p_value,
                'significant': p_value < self.alpha,
                'interpretation': 'Unequal variances' if p_value < self.alpha else 'Equal variances'
            }

        # Fligner-Killeen Test (non-parametric)
        if method in ['fligner', 'all']:
            statistic, p_value = stats.fligner(*group_data)
            results['fligner'] = {
                'test_name': 'Fligner-Killeen Test (non-parametric)',
                'statistic': statistic,
                'p_value': p_value,
                'significant': p_value < self.alpha,
                'interpretation': 'Unequal variances' if p_value < self.alpha else 'Equal variances'
            }

        # Group variances
        variances = {}
        for i, g in enumerate(groups):
            if len(group_data[i]) > 1:
                variances[g] = {
                    'variance': np.var(group_data[i], ddof=1),
                    'std': np.std(group_data[i], ddof=1),
                    'n': len(group_data[i])
                }

        results['group_variances'] = variances

        # Variance ratio (max/min)
        all_vars = [v['variance'] for v in variances.values()]
        if len(all_vars) > 1 and min(all_vars) > 0:
            variance_ratio = max(all_vars) / min(all_vars)
            results['variance_ratio'] = {
                'ratio': variance_ratio,
                'interpretation': 'Acceptable' if variance_ratio < 3 else 'Large difference (>3x)'
            }

        # Overall assessment
        violations = sum(
            1 for test in [results.get('levene'), results.get('bartlett'), results.get('fligner')]
            if test and test.get('significant', False)
        )

        if violations == 0:
            overall = "✅ Homoscedasticity assumption appears satisfied"
        elif violations == 1:
            overall = "⚠️ Possible heteroscedasticity (consider transformation)"
        else:
            overall = "❌ Significant heteroscedasticity detected"

        results['overall_assessment'] = overall
        results['recommendation'] = self._homoscedasticity_recommendation(results)

        logger.info(f"Homoscedasticity check: {overall}")

        return results

    def check_independence(
        self,
        residuals: np.ndarray,
        order: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Test for independence of observations using Durbin-Watson statistic.

        Args:
            residuals: Array of residuals from fitted model
            order: Optional array indicating the order of observations

        Returns:
            Dictionary with test results and interpretation

        Note:
            Durbin-Watson statistic ranges from 0 to 4:
            - 2 indicates no autocorrelation
            - < 2 indicates positive autocorrelation
            - > 2 indicates negative autocorrelation
            - Values around 1.5-2.5 are generally acceptable
        """
        residuals_clean = residuals[~np.isnan(residuals)]

        if len(residuals_clean) < 2:
            return {
                'error': 'Insufficient data for independence testing',
                'n': len(residuals_clean)
            }

        # Sort by order if provided
        if order is not None:
            sort_idx = np.argsort(order)
            residuals_clean = residuals_clean[sort_idx]

        # Durbin-Watson statistic
        diff = np.diff(residuals_clean)
        dw_statistic = np.sum(diff**2) / np.sum(residuals_clean**2)

        # Interpretation
        if 1.5 <= dw_statistic <= 2.5:
            interpretation = "No significant autocorrelation"
            assessment = "✅ Independence assumption appears satisfied"
        elif dw_statistic < 1.5:
            interpretation = "Positive autocorrelation detected"
            assessment = "⚠️ Observations may not be independent (positive correlation)"
        else:
            interpretation = "Negative autocorrelation detected"
            assessment = "⚠️ Observations may not be independent (negative correlation)"

        # Lag-1 autocorrelation
        if len(residuals_clean) > 1:
            lag1_corr = np.corrcoef(residuals_clean[:-1], residuals_clean[1:])[0, 1]
        else:
            lag1_corr = np.nan

        results = {
            'durbin_watson': {
                'test_name': 'Durbin-Watson Test',
                'statistic': dw_statistic,
                'interpretation': interpretation,
                'rule_of_thumb': '1.5 < DW < 2.5 indicates independence'
            },
            'lag1_autocorrelation': lag1_corr,
            'overall_assessment': assessment,
            'recommendation': self._independence_recommendation(dw_statistic)
        }

        logger.info(f"Independence check: DW={dw_statistic:.3f}, {interpretation}")

        return results

    def check_all_assumptions(
        self,
        data: pd.DataFrame,
        group_col: str,
        value_col: str,
        residuals: Optional[np.ndarray] = None
    ) -> Dict:
        """
        Check all ANOVA assumptions at once.

        Args:
            data: DataFrame with groups and values
            group_col: Column name for group labels
            value_col: Column name for values
            residuals: Optional pre-computed residuals (if None, calculated from data)

        Returns:
            Dictionary with all assumption test results

        Example:
            >>> results = checker.check_all_assumptions(df, 'treatment', 'response')
        """
        # Calculate residuals if not provided
        if residuals is None:
            # Calculate residuals as deviation from group means
            residuals = np.zeros(len(data))
            for group in data[group_col].unique():
                mask = data[group_col] == group
                group_mean = data.loc[mask, value_col].mean()
                residuals[mask] = data.loc[mask, value_col] - group_mean

        results = {
            'normality': self.check_normality(residuals, method='all'),
            'homoscedasticity': self.check_homoscedasticity(data, group_col, value_col, method='all'),
            'independence': self.check_independence(residuals)
        }

        # Overall assessment
        assessments = [
            results['normality']['overall_assessment'],
            results['homoscedasticity']['overall_assessment'],
            results['independence']['overall_assessment']
        ]

        violations = sum(1 for a in assessments if '❌' in a)
        warnings = sum(1 for a in assessments if '⚠️' in a)

        if violations > 0:
            overall = f"❌ {violations} assumption(s) violated. ANOVA results may not be valid."
        elif warnings > 0:
            overall = f"⚠️ {warnings} assumption(s) questionable. Interpret results cautiously."
        else:
            overall = "✅ All assumptions satisfied. ANOVA is appropriate."

        # Create overall_summary first
        results['overall_summary'] = {
            'assessment': overall,
            'violations': violations,
            'warnings': warnings
        }

        # Then add recommendation
        results['overall_summary']['recommendation'] = self._overall_recommendation(results)

        logger.info(f"Assumption check summary: {overall}")

        return results

    def generate_qq_plot_data(
        self,
        residuals: np.ndarray
    ) -> Dict:
        """
        Generate data for Q-Q plot (quantile-quantile plot).

        Args:
            residuals: Array of residuals

        Returns:
            Dictionary with theoretical quantiles and sample quantiles

        Example:
            >>> qq_data = checker.generate_qq_plot_data(residuals)
            >>> # Use qq_data['theoretical'] and qq_data['sample'] for plotting
        """
        residuals_clean = residuals[~np.isnan(residuals)]

        # Standardize residuals
        residuals_std = (residuals_clean - np.mean(residuals_clean)) / np.std(residuals_clean)
        residuals_sorted = np.sort(residuals_std)

        # Theoretical quantiles from standard normal
        n = len(residuals_sorted)
        theoretical_quantiles = stats.norm.ppf((np.arange(n) + 0.5) / n)

        return {
            'theoretical': theoretical_quantiles,
            'sample': residuals_sorted,
            'reference_line': {
                'slope': 1.0,
                'intercept': 0.0
            }
        }

    def generate_residual_plots_data(
        self,
        fitted_values: np.ndarray,
        residuals: np.ndarray
    ) -> Dict:
        """
        Generate data for residual diagnostic plots.

        Args:
            fitted_values: Fitted values from model
            residuals: Residuals from model

        Returns:
            Dictionary with data for multiple diagnostic plots

        Example:
            >>> plot_data = checker.generate_residual_plots_data(fitted, residuals)
        """
        # Clean data
        mask = ~(np.isnan(fitted_values) | np.isnan(residuals))
        fitted_clean = fitted_values[mask]
        residuals_clean = residuals[mask]

        # Standardized residuals
        standardized_residuals = residuals_clean / np.std(residuals_clean)

        # Square root of absolute standardized residuals (for scale-location plot)
        sqrt_abs_std_resid = np.sqrt(np.abs(standardized_residuals))

        return {
            'residual_vs_fitted': {
                'fitted': fitted_clean,
                'residuals': residuals_clean,
                'zero_line': 0
            },
            'scale_location': {
                'fitted': fitted_clean,
                'sqrt_abs_std_resid': sqrt_abs_std_resid,
                'smooth_line': self._lowess_smooth(fitted_clean, sqrt_abs_std_resid)
            },
            'standardized_residuals': standardized_residuals
        }

    def _lowess_smooth(self, x: np.ndarray, y: np.ndarray, frac: float = 0.3) -> np.ndarray:
        """Simple LOWESS smoothing for scale-location plot."""
        try:
            from scipy.signal import savgol_filter
            if len(x) > 10:
                window = min(len(x) // 3, 51)
                if window % 2 == 0:
                    window += 1
                return savgol_filter(y, window, 3)
            else:
                return y
        except:
            return y

    def _interpret_normality_test(self, p_value: float, test: str) -> str:
        """Interpret normality test p-value."""
        if p_value < self.alpha:
            return f"Reject normality (p={p_value:.4f} < {self.alpha})"
        else:
            return f"Fail to reject normality (p={p_value:.4f} ≥ {self.alpha})"

    def _normality_recommendation(self, results: Dict) -> str:
        """Generate recommendation based on normality tests."""
        skew = results.get('descriptive', {}).get('skewness', 0)

        if '❌' in results.get('overall_assessment', ''):
            if abs(skew) > 1:
                return "Consider log transformation (right-skewed) or square-root transformation"
            else:
                return "Consider non-parametric alternatives (Kruskal-Wallis test) or data transformation"
        elif '⚠️' in results.get('overall_assessment', ''):
            return "ANOVA is robust to mild non-normality, but verify with visual diagnostics (Q-Q plot)"
        else:
            return "No transformation needed"

    def _homoscedasticity_recommendation(self, results: Dict) -> str:
        """Generate recommendation based on homoscedasticity tests."""
        if '❌' in results.get('overall_assessment', ''):
            return "Consider: (1) Log transformation, (2) Welch's ANOVA (doesn't assume equal variances), or (3) Weighted least squares"
        elif '⚠️' in results.get('overall_assessment', ''):
            return "ANOVA is fairly robust to moderate heteroscedasticity, especially with equal group sizes"
        else:
            return "No adjustment needed"

    def _independence_recommendation(self, dw_statistic: float) -> str:
        """Generate recommendation based on Durbin-Watson statistic."""
        if dw_statistic < 1.5:
            return "Positive autocorrelation detected. Check if observations are ordered in time/space. Consider mixed models or time series methods."
        elif dw_statistic > 2.5:
            return "Negative autocorrelation (rare). Verify data ordering and collection process."
        else:
            return "No autocorrelation detected. Independence assumption satisfied."

    def _overall_recommendation(self, results: Dict) -> str:
        """Generate overall recommendation based on all tests."""
        violations = results['overall_summary']['violations']
        warnings = results['overall_summary']['warnings']

        if violations > 1:
            return "Multiple assumption violations detected. Consider: (1) Data transformation, (2) Non-parametric tests, or (3) Generalized linear models."
        elif violations == 1:
            return "One assumption violated. Review specific recommendations above and consider appropriate adjustments."
        elif warnings > 0:
            return "Assumptions marginally satisfied. ANOVA results are likely valid, but interpret with caution and report assumption checks."
        else:
            return "Proceed with ANOVA. All assumptions satisfied."


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Generate example data with violations
    np.random.seed(42)

    # Create data with unequal variances (heteroscedasticity)
    group_a = np.random.randn(50) * 1.0 + 10
    group_b = np.random.randn(50) * 2.0 + 12  # Double the variance
    group_c = np.random.randn(50) * 1.5 + 11

    df = pd.DataFrame({
        'treatment': ['A']*50 + ['B']*50 + ['C']*50,
        'response': np.concatenate([group_a, group_b, group_c])
    })

    # Check assumptions
    checker = AssumptionChecker(alpha=0.05)

    print("=== Checking All ANOVA Assumptions ===\n")
    results = checker.check_all_assumptions(df, 'treatment', 'response')

    print("\n1. NORMALITY:")
    print(f"   {results['normality']['overall_assessment']}")
    if 'shapiro_wilk' in results['normality']:
        print(f"   Shapiro-Wilk: p={results['normality']['shapiro_wilk']['p_value']:.4f}")

    print("\n2. HOMOSCEDASTICITY:")
    print(f"   {results['homoscedasticity']['overall_assessment']}")
    if 'levene' in results['homoscedasticity']:
        print(f"   Levene's Test: p={results['homoscedasticity']['levene']['p_value']:.4f}")

    print("\n3. INDEPENDENCE:")
    print(f"   {results['independence']['overall_assessment']}")
    print(f"   Durbin-Watson: {results['independence']['durbin_watson']['statistic']:.3f}")

    print("\n=== OVERALL SUMMARY ===")
    print(f"{results['overall_summary']['assessment']}")
    print(f"\nRecommendation: {results['overall_summary']['recommendation']}")
