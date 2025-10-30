"""
Diagnostic checks and validation module.

Provides tools for validating experimental designs and analyzing results:
- Balance checking (SMD, statistical tests, Love plots)
- Power analysis (sample size, effect size calculations)
- Assumption checking (normality, homoscedasticity, independence)
"""

from .balance_checker import BalanceChecker
from .power_analysis import PowerAnalysis
from .assumption_checks import AssumptionChecker

__all__ = [
    'BalanceChecker',
    'PowerAnalysis',
    'AssumptionChecker'
]
