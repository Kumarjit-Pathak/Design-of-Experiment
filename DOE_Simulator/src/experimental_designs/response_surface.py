"""
Response Surface Methodology (RSM)

After screening experiments identify important factors, Response Surface Methods
help find OPTIMAL factor settings by fitting a second-order model:

    Y = β₀ + Σβᵢxᵢ + Σβᵢᵢxᵢ² + ΣΣβᵢⱼxᵢxⱼ + ε

RSM can:
- Find optimal operating conditions
- Detect curvature in response surface
- Identify factor settings that maximize/minimize response

Common RSM Designs:
1. **Central Composite Design (CCD)**: Most popular, three types
   - Face-centered: α = 1 (factors stay within [-1, 1])
   - Rotatable: α = (2^k)^(1/4) (equal prediction variance at equal distance)
   - Orthogonal: α chosen for orthogonality

2. **Box-Behnken Design**: Three-level design avoiding extreme corners
   - Efficient alternative to CCD
   - Spherical design (all points equidistant from center)
   - Safer when extreme combinations are dangerous/impractical

Author: DOE Simulator Team
Date: 2025
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from itertools import product, combinations
import logging

logger = logging.getLogger(__name__)


class CentralCompositeDesign:
    """
    Central Composite Design (CCD) for Response Surface Methodology.

    CCD combines:
    - Factorial points: 2^k corners
    - Axial/star points: 2k points along axes at distance ±α
    - Center points: Replicated for pure error estimation
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize CCD generator.

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
        alpha: Optional[float] = None,
        design_type: str = 'rotatable',
        n_center_points: int = 5,
        factor_names: Optional[List[str]] = None,
        randomize: bool = True
    ) -> pd.DataFrame:
        """
        Create a Central Composite Design.

        Args:
            n_factors: Number of factors (2-10 recommended)
            alpha: Axial distance (if None, calculated based on design_type)
            design_type: 'face-centered' (α=1), 'rotatable', or 'orthogonal'
            n_center_points: Number of center point replicates (3-6 recommended)
            factor_names: Optional list of factor names
            randomize: Whether to randomize run order

        Returns:
            DataFrame containing the design matrix in coded units

        Example:
            >>> ccd = CentralCompositeDesign(random_seed=42)
            >>> design = ccd.create_design(n_factors=3, design_type='rotatable', n_center_points=5)
        """
        # Validate inputs
        if n_factors < 2:
            raise ValueError("CCD requires at least 2 factors")

        if n_factors > 10:
            logger.warning(f"CCD with {n_factors} factors requires many runs. Consider screening first.")

        # Default factor names
        if factor_names is None:
            factor_names = [f"Factor_{i+1}" for i in range(n_factors)]

        if len(factor_names) != n_factors:
            raise ValueError(f"Expected {n_factors} factor names, got {len(factor_names)}")

        # Calculate alpha based on design type
        if alpha is None:
            alpha = self._calculate_alpha(n_factors, design_type)

        logger.info(f"Creating CCD with {n_factors} factors")
        logger.info(f"Design type: {design_type}, α={alpha:.3f}")

        # 1. Generate factorial points (2^k points at corners)
        factorial_points = self._generate_factorial_points(n_factors)

        # 2. Generate axial/star points (2k points along axes)
        axial_points = self._generate_axial_points(n_factors, alpha)

        # 3. Generate center points (replicated for pure error)
        center_points = self._generate_center_points(n_factors, n_center_points)

        # Combine all points
        design_array = np.vstack([factorial_points, axial_points, center_points])

        # Create point type labels
        n_factorial = len(factorial_points)
        n_axial = len(axial_points)
        n_center = len(center_points)

        point_types = ['Factorial'] * n_factorial + ['Axial'] * n_axial + ['Center'] * n_center

        # Create DataFrame
        design_df = pd.DataFrame(design_array, columns=factor_names)
        design_df['point_type'] = point_types
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
            'design_type': f'Central Composite Design ({design_type})',
            'n_factors': n_factors,
            'alpha': alpha,
            'n_factorial_points': n_factorial,
            'n_axial_points': n_axial,
            'n_center_points': n_center,
            'total_runs': len(design_df),
            'factor_names': factor_names,
            'rotatability': 'rotatable' if design_type == 'rotatable' else 'not rotatable',
            'randomized': randomize,
            'random_seed': self.random_seed
        }

        logger.info(f"CCD created: {n_factorial} factorial + {n_axial} axial + {n_center} center = {len(design_df)} runs")

        return design_df

    def _calculate_alpha(self, n_factors: int, design_type: str) -> float:
        """
        Calculate axial distance α based on design type.

        Args:
            n_factors: Number of factors
            design_type: 'face-centered', 'rotatable', or 'orthogonal'

        Returns:
            Alpha value
        """
        if design_type == 'face-centered':
            return 1.0  # Axial points on face of cube

        elif design_type == 'rotatable':
            # α = (2^k)^(1/4) for rotatability
            return (2 ** n_factors) ** 0.25

        elif design_type == 'orthogonal':
            # Simplified orthogonal α calculation
            n_factorial = 2 ** n_factors
            n_center = 5  # Assume default
            alpha_squared = np.sqrt((n_factorial + 2 * n_factors + n_center) / 2) - n_factorial / 2
            return np.sqrt(max(1.0, alpha_squared))

        else:
            logger.warning(f"Unknown design type '{design_type}', using rotatable")
            return (2 ** n_factors) ** 0.25

    def _generate_factorial_points(self, n_factors: int) -> np.ndarray:
        """Generate 2^k factorial points at coded ±1."""
        n_runs = 2 ** n_factors
        points = np.zeros((n_runs, n_factors))

        for i in range(n_factors):
            pattern_length = 2 ** (n_factors - i - 1)
            pattern = np.tile([-1] * pattern_length + [1] * pattern_length, 2 ** i)
            points[:, i] = pattern

        return points

    def _generate_axial_points(self, n_factors: int, alpha: float) -> np.ndarray:
        """Generate 2k axial/star points at distance ±α."""
        points = []

        for i in range(n_factors):
            # Positive axial point
            point_plus = np.zeros(n_factors)
            point_plus[i] = alpha
            points.append(point_plus)

            # Negative axial point
            point_minus = np.zeros(n_factors)
            point_minus[i] = -alpha
            points.append(point_minus)

        return np.array(points)

    def _generate_center_points(self, n_factors: int, n_replicates: int) -> np.ndarray:
        """Generate center points (all factors at 0)."""
        return np.zeros((n_replicates, n_factors))

    def decode_design(
        self,
        design_df: pd.DataFrame,
        factor_ranges: Dict[str, Tuple[float, float]]
    ) -> pd.DataFrame:
        """
        Convert coded design (-1, 0, +1, ±α) to actual factor values.

        Args:
            design_df: Design in coded units
            factor_ranges: Dictionary mapping factor names to (low, high) tuples

        Returns:
            DataFrame with decoded (actual) factor values

        Example:
            >>> ranges = {'Temperature': (150, 200), 'Pressure': (10, 30)}
            >>> decoded = ccd.decode_design(design, ranges)
        """
        decoded_df = design_df.copy()

        for factor, (low, high) in factor_ranges.items():
            if factor in decoded_df.columns:
                center = (high + low) / 2
                radius = (high - low) / 2
                decoded_df[factor] = center + decoded_df[factor] * radius

        return decoded_df

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


class BoxBehnkenDesign:
    """
    Box-Behnken Design for Response Surface Methodology.

    A three-level design that:
    - Avoids extreme corner points (safer for process limits)
    - Requires fewer runs than CCD for 3+ factors
    - Forms a spherical design
    - All points at same distance from center
    """

    def __init__(self, random_seed: int = 42):
        """
        Initialize Box-Behnken Design generator.

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
        n_center_points: int = 3,
        factor_names: Optional[List[str]] = None,
        randomize: bool = True
    ) -> pd.DataFrame:
        """
        Create a Box-Behnken Design.

        Args:
            n_factors: Number of factors (3-7 recommended)
            n_center_points: Number of center point replicates
            factor_names: Optional list of factor names
            randomize: Whether to randomize run order

        Returns:
            DataFrame containing the design matrix in coded units

        Example:
            >>> bbd = BoxBehnkenDesign(random_seed=42)
            >>> design = bbd.create_design(n_factors=3, n_center_points=3)
        """
        # Validate inputs
        if n_factors < 3:
            raise ValueError("Box-Behnken Design requires at least 3 factors")

        if n_factors > 7:
            logger.warning(f"Box-Behnken with {n_factors} factors may require many runs")

        # Default factor names
        if factor_names is None:
            factor_names = [f"Factor_{i+1}" for i in range(n_factors)]

        logger.info(f"Creating Box-Behnken Design with {n_factors} factors")

        # Generate edge points (factors at ±1, 0)
        edge_points = self._generate_box_behnken_points(n_factors)

        # Generate center points
        center_points = np.zeros((n_center_points, n_factors))

        # Combine
        design_array = np.vstack([edge_points, center_points])

        # Point type labels
        n_edge = len(edge_points)
        point_types = ['Edge'] * n_edge + ['Center'] * n_center_points

        # Create DataFrame
        design_df = pd.DataFrame(design_array, columns=factor_names)
        design_df['point_type'] = point_types
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
            'design_type': 'Box-Behnken Design',
            'n_factors': n_factors,
            'n_edge_points': n_edge,
            'n_center_points': n_center_points,
            'total_runs': len(design_df),
            'factor_names': factor_names,
            'randomized': randomize,
            'random_seed': self.random_seed
        }

        logger.info(f"Box-Behnken created: {n_edge} edge + {n_center_points} center = {len(design_df)} runs")

        return design_df

    def _generate_box_behnken_points(self, n_factors: int) -> np.ndarray:
        """
        Generate Box-Behnken design points.

        For k factors, create points by:
        1. Taking all pairs of factors
        2. For each pair, set both to ±1 in 4 combinations
        3. Set remaining factors to 0

        Args:
            n_factors: Number of factors

        Returns:
            Array of design points
        """
        points = []

        # For each pair of factors
        for i, j in combinations(range(n_factors), 2):
            # Create 2^2 = 4 combinations for this pair
            for level_i, level_j in product([-1, 1], repeat=2):
                point = np.zeros(n_factors)
                point[i] = level_i
                point[j] = level_j
                points.append(point)

        return np.array(points)

    def decode_design(
        self,
        design_df: pd.DataFrame,
        factor_ranges: Dict[str, Tuple[float, float]]
    ) -> pd.DataFrame:
        """
        Convert coded design (-1, 0, +1) to actual factor values.

        Args:
            design_df: Design in coded units
            factor_ranges: Dictionary mapping factor names to (low, high) tuples

        Returns:
            DataFrame with decoded (actual) factor values
        """
        decoded_df = design_df.copy()

        for factor, (low, high) in factor_ranges.items():
            if factor in decoded_df.columns:
                center = (high + low) / 2
                radius = (high - low) / 2
                decoded_df[factor] = center + decoded_df[factor] * radius

        return decoded_df

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


# Helper function for design comparison
def compare_rsm_designs(n_factors: int) -> pd.DataFrame:
    """
    Compare CCD and Box-Behnken designs for a given number of factors.

    Args:
        n_factors: Number of factors

    Returns:
        DataFrame comparing design properties

    Example:
        >>> comparison = compare_rsm_designs(n_factors=4)
        >>> print(comparison)
    """
    # CCD (rotatable)
    ccd = CentralCompositeDesign()
    ccd_design = ccd.create_design(n_factors, design_type='rotatable', n_center_points=5, randomize=False)
    ccd_info = ccd.get_design_summary()

    # Box-Behnken (if applicable)
    if n_factors >= 3:
        bbd = BoxBehnkenDesign()
        bbd_design = bbd.create_design(n_factors, n_center_points=3, randomize=False)
        bbd_info = bbd.get_design_summary()
    else:
        bbd_info = None

    comparison = {
        'Design': ['CCD (Rotatable)', 'Box-Behnken'],
        'Total Runs': [ccd_info['total_runs'], bbd_info['total_runs'] if bbd_info else 'N/A'],
        'Factorial Points': [ccd_info['n_factorial_points'], 0],
        'Axial/Edge Points': [ccd_info['n_axial_points'], bbd_info['n_edge_points'] if bbd_info else 'N/A'],
        'Center Points': [ccd_info['n_center_points'], bbd_info['n_center_points'] if bbd_info else 'N/A'],
        'Avoids Extremes': ['No', 'Yes'],
        'Rotatability': ['Yes', 'No']
    }

    return pd.DataFrame(comparison)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    print("=== Response Surface Methodology Examples ===\n")

    # Example 1: Central Composite Design (3 factors)
    print("1. Central Composite Design (Rotatable) - 3 factors\n")

    ccd = CentralCompositeDesign(random_seed=42)
    design_ccd = ccd.create_design(n_factors=3, design_type='rotatable', n_center_points=5)

    print(design_ccd)
    print(f"\nDesign Info:")
    for key, value in ccd.get_design_summary().items():
        print(f"  {key}: {value}")

    # Example 2: Box-Behnken Design (3 factors)
    print("\n" + "="*60)
    print("\n2. Box-Behnken Design - 3 factors\n")

    bbd = BoxBehnkenDesign(random_seed=42)
    design_bbd = bbd.create_design(n_factors=3, n_center_points=3)

    print(design_bbd)
    print(f"\nDesign Info:")
    for key, value in bbd.get_design_summary().items():
        print(f"  {key}: {value}")

    # Example 3: Comparison
    print("\n" + "="*60)
    print("\n3. Design Comparison (4 factors):\n")

    comparison = compare_rsm_designs(n_factors=4)
    print(comparison.to_string(index=False))

    # Example 4: Decoding design
    print("\n" + "="*60)
    print("\n4. Decoding Design to Actual Units\n")

    factor_ranges = {
        'Factor_1': (150, 200),  # Temperature (°C)
        'Factor_2': (10, 30),    # Pressure (bar)
        'Factor_3': (5, 15)      # Catalyst (%)
    }

    decoded = ccd.decode_design(design_ccd, factor_ranges)
    print("Coded vs. Actual Values (first 5 rows):")
    print(decoded[['Factor_1', 'Factor_2', 'Factor_3', 'point_type']].head())
