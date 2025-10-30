"""
Experimental design methods module.

Provides implementations of classical and modern experimental design techniques:
- Completely Randomized Design (CRD)
- Randomized Block Design (RBD)
- Factorial Design (2^k and multi-level)
- Fractional Factorial Design (2^(k-p))
- Response Surface Methods (CCD, Box-Behnken)
"""

from .completely_randomized import CompletelyRandomizedDesign, create_crd_from_config
from .randomized_block import RandomizedBlockDesign, create_rbd_from_config
from .factorial_design import FactorialDesign
from .fractional_factorial import FractionalFactorialDesign, COMMON_DESIGNS
from .response_surface import CentralCompositeDesign, BoxBehnkenDesign, compare_rsm_designs

__all__ = [
    'CompletelyRandomizedDesign',
    'RandomizedBlockDesign',
    'FactorialDesign',
    'FractionalFactorialDesign',
    'CentralCompositeDesign',
    'BoxBehnkenDesign',
    'create_crd_from_config',
    'create_rbd_from_config',
    'compare_rsm_designs',
    'COMMON_DESIGNS'
]
