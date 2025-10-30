"""
Statistical Tests Module

This module provides wrapper functions for common statistical tests used in
Design of Experiments, including effect size calculations, power analysis,
and balance checking tests.

Author: DOE Simulator Team
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Tuple, Dict, Any, Optional
import warnings


def calculate_cohens_d(
    group1: pd.Series,
    group2: pd.Series,
    pooled: bool = True
) -> float:
    """
    Calculate Cohen's d effect size (standardized mean difference).

    Args:
        group1: First group data (e.g., treatment)
        group2: Second group data (e.g., control)
        pooled: If True, use pooled standard deviation. If False, use group2 SD.

    Returns:
        Cohen's d effect size

    Interpretation:
        |d| < 0.2: Small effect
        |d| < 0.5: Medium effect
        |d| >= 0.8: Large effect

    Example:
        >>> treatment = pd.Series([5, 6, 7, 8, 9])
        >>> control = pd.Series([3, 4, 5, 6, 7])
        >>> d = calculate_cohens_d(treatment, control)
        >>> print(f"Cohen's d: {d:.3f}")
    """
    # Remove NaN values
    group1 = group1.dropna()
    group2 = group2.dropna()

    # Calculate means
    mean1 = group1.mean()
    mean2 = group2.mean()

    # Calculate standard deviation
    if pooled:
        # Pooled standard deviation
        n1 = len(group1)
        n2 = len(group2)
        var1 = group1.var()
        var2 = group2.var()
        pooled_std = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        denominator = pooled_std
    else:
        # Use control group SD
        denominator = group2.std()

    # Avoid division by zero
    if denominator == 0:
        warnings.warn("Standard deviation is zero, cannot calculate Cohen's d", UserWarning)
        return 0.0

    cohens_d = (mean1 - mean2) / denominator

    return cohens_d


def interpret_cohens_d(d: float) -> str:
    """
    Interpret Cohen's d effect size.

    Args:
        d: Cohen's d value

    Returns:
        String interpretation
    """
    abs_d = abs(d)

    if abs_d < 0.1:
        return "Excellent balance"
    elif abs_d < 0.2:
        return "Good balance"
    elif abs_d < 0.3:
        return "Acceptable balance"
    elif abs_d < 0.5:
        return "Poor balance"
    else:
        return "Very poor balance"


def independent_ttest(
    group1: pd.Series,
    group2: pd.Series,
    equal_var: bool = True,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform independent samples t-test.

    Args:
        group1: First group data
        group2: Second group data
        equal_var: Assume equal variances (default True)
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with test results

    Example:
        >>> results = independent_ttest(treatment, control)
        >>> print(f"p-value: {results['p_value']:.4f}")
    """
    # Remove NaN values
    group1 = group1.dropna()
    group2 = group2.dropna()

    # Perform t-test
    t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=equal_var)

    # Calculate means and standard errors
    mean1 = group1.mean()
    mean2 = group2.mean()
    se1 = group1.sem()
    se2 = group2.sem()

    # Calculate confidence interval for difference
    diff = mean1 - mean2
    se_diff = np.sqrt(se1**2 + se2**2)
    df = len(group1) + len(group2) - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    ci_lower = diff - t_crit * se_diff
    ci_upper = diff + t_crit * se_diff

    results = {
        't_statistic': t_stat,
        'p_value': p_value,
        'significant': p_value < alpha,
        'mean_group1': mean1,
        'mean_group2': mean2,
        'mean_difference': diff,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'cohens_d': calculate_cohens_d(group1, group2),
        'n_group1': len(group1),
        'n_group2': len(group2)
    }

    return results


def chi_square_test(
    group1: pd.Series,
    group2: pd.Series,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform chi-square test of independence for categorical variables.

    This tests if the distribution of a categorical variable differs between two groups.

    Args:
        group1: First group categorical data (e.g., control group's gender)
        group2: Second group categorical data (e.g., treatment group's gender)
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with test results

    Example:
        >>> control_gender = df[df['group']=='control']['gender']
        >>> treatment_gender = df[df['group']=='treatment']['gender']
        >>> results = chi_square_test(control_gender, treatment_gender)
        >>> print(f"Chi-square: {results['chi2']:.2f}")
    """
    # Combine data with group labels
    combined = pd.DataFrame({
        'category': pd.concat([group1, group2], ignore_index=True),
        'group': ['group1'] * len(group1) + ['group2'] * len(group2)
    })

    # Remove NaN values
    combined = combined.dropna()

    # Create contingency table: rows=categories, columns=groups
    contingency = pd.crosstab(combined['category'], combined['group'])

    # Check if table has data
    if contingency.empty or contingency.sum().sum() == 0:
        return {
            'chi2': np.nan,
            'p_value': 1.0,
            'dof': 0,
            'significant': False,
            'cramers_v': 0.0,
            'contingency_table': contingency,
            'expected_frequencies': np.array([])
        }

    # Perform chi-square test
    chi2, p_value, dof, expected = stats.chi2_contingency(contingency)

    # Calculate Cramér's V (effect size)
    n = contingency.sum().sum()
    min_dim = min(contingency.shape[0], contingency.shape[1]) - 1
    cramers_v = np.sqrt(chi2 / (n * min_dim)) if min_dim > 0 else 0

    results = {
        'chi2': chi2,
        'p_value': p_value,
        'dof': dof,
        'significant': p_value < alpha,
        'cramers_v': cramers_v,
        'contingency_table': contingency,
        'expected_frequencies': expected
    }

    return results


def levene_test(
    *groups,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Levene's test for equality of variances.

    Args:
        *groups: Variable number of group data (Series or arrays)
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with test results

    Example:
        >>> results = levene_test(group1, group2, group3)
        >>> print(f"Equal variances: {not results['significant']}")
    """
    # Clean data (remove NaN)
    clean_groups = [np.array(group)[~np.isnan(group)] for group in groups]

    # Perform Levene's test
    statistic, p_value = stats.levene(*clean_groups)

    results = {
        'statistic': statistic,
        'p_value': p_value,
        'significant': p_value < alpha,
        'equal_variances': p_value >= alpha,
        'interpretation': 'Variances are equal' if p_value >= alpha else 'Variances differ'
    }

    return results


def shapiro_wilk_test(
    data: pd.Series,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality.

    Args:
        data: Data to test
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with test results

    Example:
        >>> results = shapiro_wilk_test(df['age'])
        >>> print(f"Normal: {results['is_normal']}")
    """
    # Remove NaN values
    data_clean = data.dropna()

    # Perform test
    statistic, p_value = stats.shapiro(data_clean)

    results = {
        'statistic': statistic,
        'p_value': p_value,
        'significant': p_value < alpha,
        'is_normal': p_value >= alpha,
        'interpretation': 'Data is normally distributed' if p_value >= alpha
                         else 'Data is not normally distributed'
    }

    return results


def anova_oneway(
    *groups,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform one-way ANOVA.

    Args:
        *groups: Variable number of group data
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with test results

    Example:
        >>> results = anova_oneway(group1, group2, group3)
        >>> print(f"F-statistic: {results['f_statistic']:.2f}")
    """
    # Clean data
    clean_groups = [np.array(group)[~np.isnan(group)] for group in groups]

    # Perform ANOVA
    f_stat, p_value = stats.f_oneway(*clean_groups)

    # Calculate effect size (eta-squared)
    # Total sum of squares
    all_data = np.concatenate(clean_groups)
    ss_total = np.sum((all_data - np.mean(all_data))**2)

    # Between-group sum of squares
    group_means = [np.mean(g) for g in clean_groups]
    group_sizes = [len(g) for g in clean_groups]
    grand_mean = np.mean(all_data)
    ss_between = sum(n * (m - grand_mean)**2 for n, m in zip(group_sizes, group_means))

    eta_squared = ss_between / ss_total if ss_total > 0 else 0

    results = {
        'f_statistic': f_stat,
        'p_value': p_value,
        'significant': p_value < alpha,
        'eta_squared': eta_squared,
        'n_groups': len(groups),
        'group_sizes': group_sizes,
        'group_means': group_means
    }

    return results


def power_analysis_ttest(
    effect_size: float,
    alpha: float = 0.05,
    power: float = 0.80,
    ratio: float = 1.0
) -> int:
    """
    Calculate required sample size for independent t-test.

    Args:
        effect_size: Expected Cohen's d
        alpha: Type I error rate (default 0.05)
        power: Desired statistical power (default 0.80)
        ratio: Ratio of group 2 to group 1 size (default 1.0 for equal groups)

    Returns:
        Required sample size per group

    Example:
        >>> n = power_analysis_ttest(effect_size=0.5, power=0.80)
        >>> print(f"Required n per group: {n}")
    """
    from scipy.stats import norm

    # Z-scores for alpha and beta
    z_alpha = norm.ppf(1 - alpha / 2)
    z_beta = norm.ppf(power)

    # Calculate sample size
    n1 = ((z_alpha + z_beta) ** 2) * (1 + 1/ratio) * (2 / (effect_size ** 2))
    n1 = int(np.ceil(n1))

    return n1


def calculate_statistical_power(
    n1: int,
    n2: int,
    effect_size: float,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for t-test given sample sizes.

    Args:
        n1: Sample size group 1
        n2: Sample size group 2
        effect_size: Expected Cohen's d
        alpha: Type I error rate (default 0.05)

    Returns:
        Statistical power (0-1)

    Example:
        >>> power = calculate_statistical_power(50, 50, 0.5)
        >>> print(f"Power: {power:.2f}")
    """
    from scipy.stats import norm, nct

    # Calculate non-centrality parameter
    ncp = effect_size * np.sqrt((n1 * n2) / (n1 + n2))

    # Degrees of freedom
    df = n1 + n2 - 2

    # Critical value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha/2, df)

    # Calculate power using non-central t-distribution
    power = 1 - nct.cdf(t_crit, df, ncp) + nct.cdf(-t_crit, df, ncp)

    return power


def proportion_test(
    count1: int,
    n1: int,
    count2: int,
    n2: int,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Test for difference in proportions between two groups.

    Args:
        count1: Number of successes in group 1
        n1: Total observations in group 1
        count2: Number of successes in group 2
        n2: Total observations in group 2
        alpha: Significance level (default 0.05)

    Returns:
        Dictionary with test results

    Example:
        >>> results = proportion_test(45, 100, 30, 100)
        >>> print(f"Proportion difference p-value: {results['p_value']:.4f}")
    """
    # Calculate proportions
    p1 = count1 / n1
    p2 = count2 / n2

    # Pooled proportion
    p_pool = (count1 + count2) / (n1 + n2)

    # Standard error
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))

    # Z-statistic
    z_stat = (p1 - p2) / se if se > 0 else 0

    # P-value (two-tailed)
    p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))

    # Confidence interval
    se_diff = np.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_crit = stats.norm.ppf(1 - alpha/2)
    ci_lower = (p1 - p2) - z_crit * se_diff
    ci_upper = (p1 - p2) + z_crit * se_diff

    results = {
        'z_statistic': z_stat,
        'p_value': p_value,
        'significant': p_value < alpha,
        'proportion1': p1,
        'proportion2': p2,
        'difference': p1 - p2,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper
    }

    return results


def format_test_results(results: Dict[str, Any]) -> str:
    """
    Format statistical test results for display.

    Args:
        results: Dictionary with test results

    Returns:
        Formatted string

    Example:
        >>> results = independent_ttest(group1, group2)
        >>> print(format_test_results(results))
    """
    lines = []
    lines.append("="*60)
    lines.append("STATISTICAL TEST RESULTS")
    lines.append("="*60)

    for key, value in results.items():
        if isinstance(value, (pd.DataFrame, np.ndarray)):
            continue  # Skip complex objects

        if isinstance(value, float):
            lines.append(f"{key}: {value:.4f}")
        elif isinstance(value, bool):
            lines.append(f"{key}: {'Yes' if value else 'No'}")
        else:
            lines.append(f"{key}: {value}")

    lines.append("="*60)

    return "\n".join(lines)


# Example usage
if __name__ == "__main__":
    # Example 1: Cohen's d
    print("Example 1: Cohen's d effect size")
    treatment = pd.Series([5, 6, 7, 8, 9, 10, 11])
    control = pd.Series([3, 4, 5, 6, 7, 8, 9])

    d = calculate_cohens_d(treatment, control)
    print(f"Cohen's d: {d:.3f}")
    print(f"Interpretation: {interpret_cohens_d(d)}")

    # Example 2: Independent t-test
    print("\n\nExample 2: Independent t-test")
    results = independent_ttest(treatment, control)
    print(format_test_results(results))

    # Example 3: Power analysis
    print("\n\nExample 3: Power analysis")
    required_n = power_analysis_ttest(effect_size=0.5, power=0.80)
    print(f"Required sample size per group: {required_n}")

    actual_power = calculate_statistical_power(50, 50, 0.5)
    print(f"Power with n=50 per group: {actual_power:.2f}")
