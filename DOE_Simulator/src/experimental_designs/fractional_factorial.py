"""
Fractional Factorial Design (2^(k-p))

When the number of factors is large (k > 5), a full factorial design (2^k) requires
too many experimental runs. Fractional factorial designs test a carefully selected
FRACTION of all possible treatment combinations, dramatically reducing experimental cost.

Key Concepts:
- 2^(k-p) design: k factors tested in 2^(k-p) runs (1/(2^p) fraction of full factorial)
- Resolution: Indicates which effects are confounded (aliased)
- Alias Structure: Pattern of effect confounding
- Generators: Define which fraction to use

Resolution Levels:
- Resolution III: Main effects confounded with 2-way interactions (use for screening only)
- Resolution IV: Main effects clear, but 2-way interactions confounded with each other
- Resolution V: Main effects and 2-way interactions clear (gold standard)

Example: 2^(7-4) design
- 7 factors, only 16 runs (instead of 128 for full factorial)
- 1/8 fraction of full design
- Can estimate main effects efficiently

Author: DOE Simulator Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from itertools import product, combinations
import logging

logger = logging.getLogger(__name__)


class FractionalFactorialDesign:
    """
    Fractional Factorial Design (2^(k-p)) implementation.

    Supports:
    - Two-level fractional factorial designs
    - Resolution III, IV, and V designs
    - Alias structure generation
    - Effect estimation from fractional designs
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize Fractional Factorial Design generator.

        Args:
            random_seed: Random seed for reproducibility
        """
        self.random_seed = random_seed
        np.random.seed(random_seed)
        self.design_matrix = None
        self.design_info = {}

    def create_design(
        self,
        n_factors: int,
        n_runs: int,
        factor_names: Optional[List[str]] = None,
        generators: Optional[List[str]] = None,
        randomize: bool = True
    ) -> pd.DataFrame:
        """
        Create a fractional factorial design.

        Args:
            n_factors: Total number of factors (k)
            n_runs: Number of experimental runs (must be power of 2)
            factor_names: Optional list of factor names (default: A, B, C, ...)
            generators: Optional list of generator expressions (e.g., ['D=ABC'])
            randomize: Whether to randomize run order

        Returns:
            DataFrame containing the design matrix

        Example:
            >>> ffd = FractionalFactorialDesign(random_seed=42)
            >>> # 2^(5-2) design: 5 factors in 8 runs (Resolution III)
            >>> design = ffd.create_design(n_factors=5, n_runs=8)

            >>> # With custom generators for Resolution IV
            >>> design = ffd.create_design(
            ...     n_factors=5,
            ...     n_runs=8,
            ...     generators=['D=AB', 'E=AC']
            ... )
        """
        # Validate inputs
        if not self._is_power_of_2(n_runs):
            raise ValueError(f"n_runs must be a power of 2 (got {n_runs})")

        # Calculate fraction
        p = int(np.log2(2**n_factors / n_runs))
        n_base_factors = n_factors - p

        if p < 0:
            raise ValueError(f"n_runs ({n_runs}) exceeds full factorial size (2^{n_factors} = {2**n_factors})")

        logger.info(f"Creating 2^({n_factors}-{p}) fractional factorial design")
        logger.info(f"Base factors: {n_base_factors}, Fraction: 1/{2**p}")

        # Default factor names
        if factor_names is None:
            factor_names = [chr(65 + i) for i in range(n_factors)]  # A, B, C, ...

        if len(factor_names) != n_factors:
            raise ValueError(f"Expected {n_factors} factor names, got {len(factor_names)}")

        # Generate base factorial design (full factorial for base factors)
        base_design = self._generate_full_factorial(n_base_factors)

        # Add fractional factors using generators
        if generators is None:
            generators = self._default_generators(n_factors, p, factor_names)

        design_array = self._apply_generators(base_design, generators, factor_names)

        # Create DataFrame
        design_df = pd.DataFrame(
            design_array,
            columns=factor_names
        )

        # Convert to +1/-1 coding
        design_df = design_df.replace({0: -1, 1: 1})

        # Add standard order
        design_df['std_order'] = range(1, len(design_df) + 1)

        # Randomize if requested
        if randomize:
            design_df['run_order'] = np.random.permutation(len(design_df)) + 1
            design_df = design_df.sort_values('run_order').reset_index(drop=True)
        else:
            design_df['run_order'] = design_df['std_order']

        # Calculate design properties
        resolution = self._calculate_resolution(generators, factor_names)
        alias_structure = self._generate_alias_structure(generators, factor_names, n_factors)

        # Store design information
        self.design_matrix = design_df
        self.design_info = {
            'design_type': f'2^({n_factors}-{p}) Fractional Factorial',
            'n_factors': n_factors,
            'n_runs': n_runs,
            'fraction': f'1/{2**p}',
            'p': p,
            'n_base_factors': n_base_factors,
            'factor_names': factor_names,
            'generators': generators,
            'resolution': resolution,
            'alias_structure': alias_structure,
            'randomized': randomize,
            'random_seed': self.random_seed
        }

        logger.info(f"Design created: Resolution {resolution}")
        logger.info(f"Generators: {generators}")

        return design_df

    def _generate_full_factorial(self, n_factors: int) -> np.ndarray:
        """Generate full factorial design for n factors."""
        n_runs = 2 ** n_factors
        design = np.zeros((n_runs, n_factors), dtype=int)

        for i in range(n_factors):
            # Create alternating pattern for each factor
            pattern_length = 2 ** (n_factors - i - 1)
            pattern = np.tile([0] * pattern_length + [1] * pattern_length, 2 ** i)
            design[:, i] = pattern

        return design

    def _apply_generators(
        self,
        base_design: np.ndarray,
        generators: List[str],
        factor_names: List[str]
    ) -> np.ndarray:
        """
        Apply generator expressions to create fractional design.

        Args:
            base_design: Full factorial design for base factors
            generators: List of generator expressions (e.g., ['D=ABC'])
            factor_names: List of all factor names

        Returns:
            Complete design matrix with generated factors
        """
        n_base_factors = base_design.shape[1]
        n_factors = len(factor_names)
        n_runs = base_design.shape[0]

        # Initialize full design
        design = np.zeros((n_runs, n_factors), dtype=int)
        design[:, :n_base_factors] = base_design

        # Apply each generator
        for generator in generators:
            if '=' not in generator:
                continue

            # Parse generator (e.g., "D=ABC" or "E=AB")
            left, right = generator.split('=')
            target_factor = left.strip()
            source_factors = right.strip()

            # Find target factor index
            if target_factor not in factor_names:
                logger.warning(f"Generator factor {target_factor} not in factor_names, skipping")
                continue

            target_idx = factor_names.index(target_factor)

            # Calculate generated factor as product of source factors (XOR for binary)
            generated_column = np.ones(n_runs, dtype=int)
            for source_factor in source_factors:
                if source_factor in factor_names:
                    source_idx = factor_names.index(source_factor)
                    if source_idx < n_base_factors:
                        # XOR operation (multiplication in coded form)
                        generated_column = (generated_column + design[:, source_idx]) % 2

            design[:, target_idx] = generated_column

        return design

    def _default_generators(
        self,
        n_factors: int,
        p: int,
        factor_names: List[str]
    ) -> List[str]:
        """
        Generate default generators for fractional factorial design.

        Uses standard generators that maximize resolution.

        Args:
            n_factors: Total number of factors
            p: Fraction parameter (design is 2^(k-p))
            factor_names: List of factor names

        Returns:
            List of generator expressions
        """
        n_base = n_factors - p

        # Standard high-resolution generators
        standard_generators = {
            # 2^(4-1) = Resolution IV
            (4, 1): ['D=ABC'],

            # 2^(5-1) = Resolution V
            (5, 1): ['E=ABCD'],

            # 2^(5-2) = Resolution III
            (5, 2): ['D=AB', 'E=AC'],

            # 2^(6-1) = Resolution VI
            (6, 1): ['F=ABCDE'],

            # 2^(6-2) = Resolution IV
            (6, 2): ['E=ABC', 'F=BCD'],

            # 2^(6-3) = Resolution III
            (6, 3): ['D=AB', 'E=AC', 'F=BC'],

            # 2^(7-1) = Resolution VII
            (7, 1): ['G=ABCDEF'],

            # 2^(7-2) = Resolution IV
            (7, 2): ['F=ABCD', 'G=ABCE'],

            # 2^(7-3) = Resolution IV
            (7, 3): ['E=ABC', 'F=BCD', 'G=ACD'],

            # 2^(7-4) = Resolution III
            (7, 4): ['D=AB', 'E=AC', 'F=BC', 'G=ABC'],

            # 2^(8-4) = Resolution IV
            (8, 4): ['E=BCD', 'F=ACD', 'G=ABC', 'H=ABD']
        }

        key = (n_factors, p)
        if key in standard_generators:
            return standard_generators[key]
        else:
            # Generate simple generators (Resolution III)
            generators = []
            base_factors = factor_names[:n_base]

            for i in range(p):
                target_factor = factor_names[n_base + i]
                # Simple two-factor interaction
                if i < len(base_factors) - 1:
                    source_expr = base_factors[i] + base_factors[i + 1]
                else:
                    source_expr = base_factors[0] + base_factors[1]

                generators.append(f"{target_factor}={source_expr}")

            logger.warning(f"Using simple generators (Resolution III) for 2^({n_factors}-{p})")
            return generators

    def _calculate_resolution(
        self,
        generators: List[str],
        factor_names: List[str]
    ) -> int:
        """
        Calculate design resolution from generators.

        Resolution is the length of the shortest word in the defining relation.

        Args:
            generators: List of generator expressions
            factor_names: List of factor names

        Returns:
            Resolution (III, IV, V, etc.)
        """
        # Count letters in generator right-hand sides
        word_lengths = []

        for gen in generators:
            if '=' not in gen:
                continue
            _, rhs = gen.split('=')
            # Count number of factors in the generator
            word_lengths.append(len(rhs.strip()))

        if not word_lengths:
            return 2  # Full factorial

        # Resolution is minimum word length + 1
        # (because defining relation includes the left-hand side)
        return min(word_lengths) + 1

    def _generate_alias_structure(
        self,
        generators: List[str],
        factor_names: List[str],
        n_factors: int
    ) -> Dict[str, List[str]]:
        """
        Generate alias structure showing which effects are confounded.

        Args:
            generators: List of generator expressions
            factor_names: List of factor names
            n_factors: Number of factors

        Returns:
            Dictionary mapping effects to their aliases
        """
        alias_structure = {}

        # Main effects
        for factor in factor_names:
            aliases = [factor]

            # Check if main effect is aliased with anything from generators
            for gen in generators:
                if '=' not in gen:
                    continue
                lhs, rhs = gen.split('=')
                lhs = lhs.strip()
                rhs = rhs.strip()

                # If this factor is in generator, it's aliased
                if factor == lhs:
                    aliases.append(rhs)
                elif factor in rhs:
                    # Remove this factor from RHS to find alias
                    remaining = rhs.replace(factor, '')
                    if remaining:
                        aliases.append(lhs + remaining if lhs not in remaining else remaining)

            alias_structure[factor] = list(set(aliases))

        # Two-way interactions (simplified - show a few key ones)
        base_factors = factor_names[:min(4, n_factors)]  # Limit to avoid explosion
        for f1, f2 in combinations(base_factors, 2):
            interaction = f"{f1}{f2}"
            alias_structure[interaction] = [interaction]  # Simplified

        return alias_structure

    def _is_power_of_2(self, n: int) -> bool:
        """Check if n is a power of 2."""
        return n > 0 and (n & (n - 1)) == 0

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


# Pre-defined catalog of common fractional factorial designs
COMMON_DESIGNS = {
    '2^(4-1)_IV': {
        'n_factors': 4,
        'n_runs': 8,
        'generators': ['D=ABC'],
        'resolution': 'IV',
        'description': '4 factors in 8 runs, Resolution IV'
    },
    '2^(5-1)_V': {
        'n_factors': 5,
        'n_runs': 16,
        'generators': ['E=ABCD'],
        'resolution': 'V',
        'description': '5 factors in 16 runs, Resolution V (excellent)'
    },
    '2^(5-2)_III': {
        'n_factors': 5,
        'n_runs': 8,
        'generators': ['D=AB', 'E=AC'],
        'resolution': 'III',
        'description': '5 factors in 8 runs, Resolution III (screening only)'
    },
    '2^(7-4)_III': {
        'n_factors': 7,
        'n_runs': 8,
        'generators': ['D=AB', 'E=AC', 'F=BC', 'G=ABC'],
        'resolution': 'III',
        'description': '7 factors in 8 runs, Resolution III (screening)'
    },
    '2^(7-3)_IV': {
        'n_factors': 7,
        'n_runs': 16,
        'generators': ['E=ABC', 'F=BCD', 'G=ACD'],
        'resolution': 'IV',
        'description': '7 factors in 16 runs, Resolution IV'
    }
}


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("=== Fractional Factorial Design Examples ===\n")

    # Example 1: 2^(5-2) Resolution III design (screening)
    print("1. Screening Design: 2^(5-2) - 5 factors in 8 runs")
    print("   Resolution III - Use for initial screening\n")

    ffd = FractionalFactorialDesign(random_seed=42)
    design = ffd.create_design(n_factors=5, n_runs=8)

    print(design)
    print(f"\nDesign Info:")
    print(f"  Resolution: {ffd.design_info['resolution']}")
    print(f"  Generators: {ffd.design_info['generators']}")
    print(f"  Fraction: {ffd.design_info['fraction']}")

    # Example 2: 2^(7-3) Resolution IV design
    print("\n" + "="*60)
    print("\n2. Resolution IV Design: 2^(7-3) - 7 factors in 16 runs")
    print("   Resolution IV - Main effects clear from 2-way interactions\n")

    ffd2 = FractionalFactorialDesign(random_seed=42)
    design2 = ffd2.create_design(n_factors=7, n_runs=16)

    print(design2.head(10))
    print(f"\nDesign Info:")
    print(f"  Resolution: {ffd2.design_info['resolution']}")
    print(f"  Generators: {ffd2.design_info['generators']}")

    print("\n" + "="*60)
    print("\n3. Common Design Catalog:")
    for name, info in COMMON_DESIGNS.items():
        print(f"\n{name}: {info['description']}")
        print(f"  Generators: {info['generators']}")
