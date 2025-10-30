"""
Power Analysis Module

Statistical power is the probability of correctly rejecting a false null hypothesis
(i.e., detecting a true effect when it exists). Power analysis helps determine:
- Required sample size for desired power
- Power achieved with given sample size
- Minimum detectable effect size

The Four Horsemen of Power Analysis:
1. Significance level (α): Type I error rate (usually 0.05)
2. Power (1-β): Probability of detecting true effect (usually 0.80)
3. Effect size: Magnitude of the effect (Cohen's d, η², etc.)
4. Sample size: Number of observations

**Key Principle:** Specify any three, calculate the fourth.

Common Effect Size Conventions (Cohen, 1988):
- Small: d = 0.2, η² = 0.01, r = 0.1
- Medium: d = 0.5, η² = 0.06, r = 0.3
- Large: d = 0.8, η² = 0.14, r = 0.5

Author: DOE Simulator Team
Date: 2025
"""

import numpy as np
from scipy import stats
from typing import Dict, Optional, Union, Tuple
import logging

logger = logging.getLogger(__name__)


class PowerAnalysis:
    """
    Power analysis for common experimental designs.

    Supports:
    - Two-sample t-tests (independent groups)
    - One-way ANOVA (multiple groups)
    - Chi-square tests (categorical data)
    """

    def __init__(self, alpha: float = 0.05):
        """
        Initialize power analysis with significance level.

        Args:
            alpha: Significance level (Type I error rate), typically 0.05
        """
        self.alpha = alpha

    def power_two_sample_ttest(
        self,
        effect_size: Optional[float] = None,
        n_per_group: Optional[int] = None,
        power: Optional[float] = None,
        ratio: float = 1.0,
        alternative: str = 'two-sided'
    ) -> Dict:
        """
        Power analysis for two-sample t-test (independent groups).

        Specify any 2 of: effect_size, n_per_group, power.
        The third will be calculated.

        Args:
            effect_size: Cohen's d (standardized mean difference)
            n_per_group: Sample size per group
            power: Statistical power (1 - β), typically 0.80
            ratio: Ratio of group sizes (n2/n1), default 1.0 for equal groups
            alternative: 'two-sided' or 'one-sided'

        Returns:
            Dictionary with all power analysis parameters

        Example:
            >>> pa = PowerAnalysis(alpha=0.05)
            >>> # Calculate required sample size for d=0.5, power=0.80
            >>> result = pa.power_two_sample_ttest(effect_size=0.5, power=0.80)
            >>> print(f"Required n per group: {result['n_per_group']}")
        """
        # Validate inputs
        specified = sum([effect_size is not None, n_per_group is not None, power is not None])

        if specified < 2:
            raise ValueError("Must specify at least 2 of: effect_size, n_per_group, power")

        if specified == 3:
            logger.warning("All 3 parameters specified. Will calculate power as verification.")

        # Critical value for significance test
        if alternative == 'two-sided':
            z_alpha = stats.norm.ppf(1 - self.alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - self.alpha)

        # Calculate missing parameter
        if n_per_group is None:
            # Calculate required sample size
            if power is None or effect_size is None:
                raise ValueError("Must specify both effect_size and power to calculate n")

            z_beta = stats.norm.ppf(power)

            # Formula: n = (z_α + z_β)² × (1 + 1/r) / d²
            n_per_group = int(np.ceil(
                ((z_alpha + z_beta) ** 2) * (1 + 1/ratio) / (effect_size ** 2)
            ))

            # Verify power with calculated n
            ncp = effect_size * np.sqrt(n_per_group * ratio / (1 + ratio))
            if alternative == 'two-sided':
                calculated_power = 1 - stats.norm.cdf(z_alpha - ncp) + stats.norm.cdf(-z_alpha - ncp)
            else:
                calculated_power = 1 - stats.norm.cdf(z_alpha - ncp)

        elif effect_size is None:
            # Calculate minimum detectable effect size
            if power is None or n_per_group is None:
                raise ValueError("Must specify both n_per_group and power to calculate effect_size")

            z_beta = stats.norm.ppf(power)

            # Rearrange formula: d = (z_α + z_β) / sqrt(n × r / (1 + r))
            effect_size = (z_alpha + z_beta) / np.sqrt(n_per_group * ratio / (1 + ratio))
            calculated_power = power  # By definition

        else:  # power is None
            # Calculate achieved power
            if effect_size is None or n_per_group is None:
                raise ValueError("Must specify both effect_size and n_per_group to calculate power")

            # Non-centrality parameter
            ncp = effect_size * np.sqrt(n_per_group * ratio / (1 + ratio))

            # Calculate power
            if alternative == 'two-sided':
                calculated_power = 1 - stats.norm.cdf(z_alpha - ncp) + stats.norm.cdf(-z_alpha - ncp)
            else:
                calculated_power = 1 - stats.norm.cdf(z_alpha - ncp)

            power = calculated_power

        # Total sample size
        n_total = int(n_per_group * (1 + ratio))

        # Effect size interpretation
        effect_interpretation = self._interpret_cohens_d(effect_size)

        # Power interpretation
        if calculated_power >= 0.90:
            power_interpretation = "Excellent (≥90%)"
        elif calculated_power >= 0.80:
            power_interpretation = "Good (≥80%)"
        elif calculated_power >= 0.70:
            power_interpretation = "Acceptable (≥70%)"
        else:
            power_interpretation = "Underpowered (<70%)"

        result = {
            'test': 'Two-sample t-test',
            'alpha': self.alpha,
            'alternative': alternative,
            'effect_size': effect_size,
            'effect_size_interpretation': effect_interpretation,
            'n_per_group': n_per_group,
            'n_group1': n_per_group,
            'n_group2': int(n_per_group * ratio),
            'n_total': n_total,
            'ratio': ratio,
            'power': calculated_power,
            'power_interpretation': power_interpretation,
            'beta': 1 - calculated_power,  # Type II error
            'critical_value': z_alpha
        }

        logger.info(f"Two-sample t-test power analysis: n={n_per_group} per group, d={effect_size:.3f}, power={calculated_power:.3f}")

        return result

    def power_anova(
        self,
        effect_size: Optional[float] = None,
        n_per_group: Optional[int] = None,
        power: Optional[float] = None,
        n_groups: int = 3
    ) -> Dict:
        """
        Power analysis for one-way ANOVA.

        Args:
            effect_size: Cohen's f (effect size for ANOVA)
                        f = sqrt(η² / (1 - η²))
            n_per_group: Sample size per group
            power: Statistical power
            n_groups: Number of groups

        Returns:
            Dictionary with power analysis results

        Example:
            >>> # Calculate power for n=30 per group, medium effect (f=0.25), 4 groups
            >>> result = pa.power_anova(effect_size=0.25, n_per_group=30, n_groups=4)
        """
        specified = sum([effect_size is not None, n_per_group is not None, power is not None])

        if specified < 2:
            raise ValueError("Must specify at least 2 of: effect_size, n_per_group, power")

        # Degrees of freedom
        df_between = n_groups - 1

        # Critical F-value
        if n_per_group is not None:
            df_within = n_groups * (n_per_group - 1)
            f_crit = stats.f.ppf(1 - self.alpha, df_between, df_within)
        else:
            f_crit = None

        # Calculate missing parameter
        if n_per_group is None:
            # Calculate required sample size
            # Iterative approach
            if power is None or effect_size is None:
                raise ValueError("Must specify both effect_size and power")

            # Start with initial guess
            n_guess = 10
            for _ in range(100):
                df_within = n_groups * (n_guess - 1)
                f_crit = stats.f.ppf(1 - self.alpha, df_between, df_within)

                # Non-centrality parameter
                lambda_ncp = (effect_size ** 2) * n_guess * n_groups

                # Power from non-central F distribution
                calc_power = 1 - stats.ncf.cdf(f_crit, df_between, df_within, lambda_ncp)

                if calc_power >= power:
                    break

                n_guess += 1

            n_per_group = n_guess
            calculated_power = calc_power

        elif effect_size is None:
            # Calculate minimum detectable effect size
            if power is None or n_per_group is None:
                raise ValueError("Must specify both n_per_group and power")

            # Iterative search for effect size
            f_guess = 0.01
            for _ in range(1000):
                lambda_ncp = (f_guess ** 2) * n_per_group * n_groups
                df_within = n_groups * (n_per_group - 1)
                f_crit = stats.f.ppf(1 - self.alpha, df_between, df_within)

                calc_power = 1 - stats.ncf.cdf(f_crit, df_between, df_within, lambda_ncp)

                if calc_power >= power:
                    break

                f_guess += 0.001

            effect_size = f_guess
            calculated_power = calc_power

        else:  # power is None
            # Calculate achieved power
            df_within = n_groups * (n_per_group - 1)
            lambda_ncp = (effect_size ** 2) * n_per_group * n_groups
            f_crit = stats.f.ppf(1 - self.alpha, df_between, df_within)

            calculated_power = 1 - stats.ncf.cdf(f_crit, df_between, df_within, lambda_ncp)
            power = calculated_power

        # Convert Cohen's f to eta-squared
        eta_squared = (effect_size ** 2) / (1 + effect_size ** 2)

        result = {
            'test': 'One-way ANOVA',
            'alpha': self.alpha,
            'n_groups': n_groups,
            'effect_size_f': effect_size,
            'effect_size_eta_squared': eta_squared,
            'effect_size_interpretation': self._interpret_cohens_f(effect_size),
            'n_per_group': n_per_group,
            'n_total': n_per_group * n_groups,
            'df_between': df_between,
            'df_within': n_groups * (n_per_group - 1),
            'power': calculated_power,
            'power_interpretation': "Good" if calculated_power >= 0.80 else "Underpowered",
            'beta': 1 - calculated_power
        }

        logger.info(f"ANOVA power analysis: n={n_per_group} per group, k={n_groups} groups, f={effect_size:.3f}, power={calculated_power:.3f}")

        return result

    def sample_size_two_proportions(
        self,
        p1: float,
        p2: float,
        power: float = 0.80,
        ratio: float = 1.0,
        alternative: str = 'two-sided'
    ) -> Dict:
        """
        Calculate sample size for comparing two proportions.

        Args:
            p1: Proportion in group 1
            p2: Proportion in group 2
            power: Desired power
            ratio: Sample size ratio (n2/n1)
            alternative: 'two-sided' or 'one-sided'

        Returns:
            Dictionary with sample size calculations

        Example:
            >>> # Sample size to detect difference between 10% and 15% conversion rates
            >>> result = pa.sample_size_two_proportions(p1=0.10, p2=0.15, power=0.80)
        """
        # Pooled proportion
        p_pooled = (p1 + ratio * p2) / (1 + ratio)

        # Effect size (standardized difference)
        effect_size = abs(p1 - p2) / np.sqrt(p_pooled * (1 - p_pooled))

        # Critical values
        if alternative == 'two-sided':
            z_alpha = stats.norm.ppf(1 - self.alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - self.alpha)

        z_beta = stats.norm.ppf(power)

        # Calculate sample size
        n1 = int(np.ceil(
            ((z_alpha * np.sqrt(p_pooled * (1 - p_pooled) * (1 + 1/ratio)) +
              z_beta * np.sqrt(p1 * (1 - p1) + p2 * (1 - p2) / ratio)) ** 2) /
            ((p1 - p2) ** 2)
        ))

        n2 = int(n1 * ratio)

        result = {
            'test': 'Two-proportions z-test',
            'alpha': self.alpha,
            'alternative': alternative,
            'p1': p1,
            'p2': p2,
            'difference': p2 - p1,
            'relative_improvement': (p2 - p1) / p1 * 100 if p1 > 0 else np.inf,
            'effect_size': effect_size,
            'n_group1': n1,
            'n_group2': n2,
            'n_total': n1 + n2,
            'ratio': ratio,
            'power': power
        }

        logger.info(f"Two-proportions test: n1={n1}, n2={n2}, p1={p1:.3f}, p2={p2:.3f}, power={power:.3f}")

        return result

    def _interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size."""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"

    def _interpret_cohens_f(self, f: float) -> str:
        """Interpret Cohen's f effect size for ANOVA."""
        if f < 0.10:
            return "negligible"
        elif f < 0.25:
            return "small"
        elif f < 0.40:
            return "medium"
        else:
            return "large"

    def create_power_curve(
        self,
        effect_sizes: np.ndarray,
        n_per_group: int,
        test_type: str = 'ttest',
        **kwargs
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate power curve data for visualization.

        Args:
            effect_sizes: Array of effect sizes to evaluate
            n_per_group: Sample size per group
            test_type: 'ttest' or 'anova'
            **kwargs: Additional parameters (e.g., n_groups for ANOVA)

        Returns:
            Tuple of (effect_sizes, power_values)

        Example:
            >>> effect_sizes = np.linspace(0, 1, 50)
            >>> es, power = pa.create_power_curve(effect_sizes, n_per_group=50)
        """
        power_values = []

        for es in effect_sizes:
            if test_type == 'ttest':
                result = self.power_two_sample_ttest(
                    effect_size=es,
                    n_per_group=n_per_group
                )
            elif test_type == 'anova':
                result = self.power_anova(
                    effect_size=es,
                    n_per_group=n_per_group,
                    n_groups=kwargs.get('n_groups', 3)
                )
            else:
                raise ValueError(f"Unknown test type: {test_type}")

            power_values.append(result['power'])

        return effect_sizes, np.array(power_values)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    pa = PowerAnalysis(alpha=0.05)

    print("=== Power Analysis Examples ===\n")

    # Example 1: Calculate sample size for t-test
    print("1. Two-sample t-test: Calculate required sample size")
    result = pa.power_two_sample_ttest(effect_size=0.5, power=0.80)
    print(f"   Effect size: {result['effect_size']:.3f} ({result['effect_size_interpretation']})")
    print(f"   Required n per group: {result['n_per_group']}")
    print(f"   Total sample size: {result['n_total']}")
    print(f"   Achieved power: {result['power']:.3f}\n")

    # Example 2: Calculate power for given sample size
    print("2. Two-sample t-test: Calculate power for n=50 per group")
    result = pa.power_two_sample_ttest(effect_size=0.5, n_per_group=50)
    print(f"   Sample size: {result['n_per_group']} per group")
    print(f"   Effect size: {result['effect_size']:.3f}")
    print(f"   Achieved power: {result['power']:.3f} ({result['power_interpretation']})\n")

    # Example 3: ANOVA sample size
    print("3. One-way ANOVA: Calculate sample size for 4 groups")
    result = pa.power_anova(effect_size=0.25, power=0.80, n_groups=4)
    print(f"   Number of groups: {result['n_groups']}")
    print(f"   Effect size (f): {result['effect_size_f']:.3f} ({result['effect_size_interpretation']})")
    print(f"   Required n per group: {result['n_per_group']}")
    print(f"   Total sample size: {result['n_total']}")
    print(f"   Achieved power: {result['power']:.3f}\n")

    # Example 4: Two proportions
    print("4. Two proportions: Detect conversion rate improvement")
    result = pa.sample_size_two_proportions(p1=0.10, p2=0.15, power=0.80)
    print(f"   Baseline rate: {result['p1']*100:.1f}%")
    print(f"   Target rate: {result['p2']*100:.1f}%")
    print(f"   Relative improvement: {result['relative_improvement']:.1f}%")
    print(f"   Required n per group: {result['n_group1']:,}")
    print(f"   Total sample size: {result['n_total']:,}")
