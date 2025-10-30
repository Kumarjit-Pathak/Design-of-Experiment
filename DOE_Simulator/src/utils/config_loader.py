"""
Configuration Loader Module

This module provides functions to load and validate JSON configuration files
for DOE experiments. It ensures all required parameters are present and
provides sensible defaults where appropriate.

Author: DOE Simulator Team
"""

import json
import os
from typing import Dict, Any, List, Optional
import warnings


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file.

    Args:
        config_path: Path to JSON configuration file

    Returns:
        Dictionary containing configuration parameters

    Raises:
        ConfigError: If config file not found or invalid JSON

    Example:
        >>> config = load_config('config/sampling_config.json')
        >>> print(config['sample_size'])
        1000
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"Configuration file not found: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
    except json.JSONDecodeError as e:
        raise ConfigError(f"Invalid JSON in config file: {str(e)}")

    return config


def validate_config(
    config: Dict[str, Any],
    required_keys: List[str],
    optional_keys: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate configuration and provide defaults for optional parameters.

    Args:
        config: Configuration dictionary to validate
        required_keys: List of required parameter names
        optional_keys: Dictionary of optional parameters with default values

    Returns:
        Validated and completed configuration dictionary

    Raises:
        ConfigError: If required keys are missing

    Example:
        >>> config = {'data_path': 'data.csv', 'sample_size': 100}
        >>> required = ['data_path', 'sample_size']
        >>> optional = {'random_seed': 42, 'output_path': None}
        >>> validated = validate_config(config, required, optional)
    """
    # Check required keys
    missing_keys = [key for key in required_keys if key not in config]
    if missing_keys:
        raise ConfigError(f"Missing required configuration keys: {missing_keys}")

    # Add optional keys with defaults
    if optional_keys:
        for key, default_value in optional_keys.items():
            if key not in config:
                config[key] = default_value
                warnings.warn(
                    f"Using default value for '{key}': {default_value}",
                    UserWarning
                )

    return config


def validate_data_path(data_path: str) -> str:
    """
    Validate that data file exists.

    Args:
        data_path: Path to data file

    Returns:
        Validated data path

    Raises:
        ConfigError: If data file not found
    """
    if not os.path.exists(data_path):
        raise ConfigError(f"Data file not found: {data_path}")

    if not data_path.endswith('.csv'):
        warnings.warn(
            f"Data file does not have .csv extension: {data_path}",
            UserWarning
        )

    return data_path


def validate_sample_size(sample_size: int, max_size: Optional[int] = None) -> int:
    """
    Validate sample size parameter.

    Args:
        sample_size: Requested sample size
        max_size: Maximum allowed sample size (optional)

    Returns:
        Validated sample size

    Raises:
        ConfigError: If sample size is invalid
    """
    if not isinstance(sample_size, int):
        raise ConfigError(f"Sample size must be an integer, got {type(sample_size)}")

    if sample_size <= 0:
        raise ConfigError(f"Sample size must be positive, got {sample_size}")

    if max_size and sample_size > max_size:
        warnings.warn(
            f"Sample size ({sample_size}) exceeds maximum ({max_size}). "
            f"Using maximum size.",
            UserWarning
        )
        sample_size = max_size

    return sample_size


def validate_random_seed(random_seed: Optional[int]) -> Optional[int]:
    """
    Validate random seed parameter.

    Args:
        random_seed: Random seed value (can be None)

    Returns:
        Validated random seed

    Raises:
        ConfigError: If seed is invalid
    """
    if random_seed is None:
        return None

    if not isinstance(random_seed, int):
        raise ConfigError(f"Random seed must be an integer, got {type(random_seed)}")

    if random_seed < 0:
        raise ConfigError(f"Random seed must be non-negative, got {random_seed}")

    return random_seed


def validate_column_names(
    columns: List[str],
    available_columns: List[str],
    param_name: str = "columns"
) -> List[str]:
    """
    Validate that requested columns exist in dataset.

    Args:
        columns: List of requested column names
        available_columns: List of available column names
        param_name: Name of parameter for error messages

    Returns:
        Validated column list

    Raises:
        ConfigError: If columns are invalid
    """
    if not columns:
        raise ConfigError(f"{param_name} cannot be empty")

    missing_columns = [col for col in columns if col not in available_columns]
    if missing_columns:
        raise ConfigError(
            f"Columns not found in dataset for {param_name}: {missing_columns}"
        )

    return columns


def create_default_config(
    methodology: str,
    data_path: str = "data/raw/ecommerce_data.csv",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a default configuration for a given methodology.

    Args:
        methodology: Name of DOE methodology
        data_path: Path to data file
        **kwargs: Additional parameters to override defaults

    Returns:
        Configuration dictionary

    Example:
        >>> config = create_default_config(
        ...     'simple_random_sampling',
        ...     sample_size=1000
        ... )
    """
    # Base configuration
    config = {
        "methodology": methodology,
        "data_path": data_path,
        "random_seed": 42,
        "output_path": None
    }

    # Methodology-specific defaults
    if 'sampling' in methodology:
        config.update({
            "sample_size": 1000,
            "stratify_by": None,
            "cluster_by": None
        })

    elif 'design' in methodology or 'randomized' in methodology:
        config.update({
            "treatment_column": "treatment_group",
            "control_proportion": 0.5,
            "block_by": None,
            "balance_columns": ["age", "gender", "income_level"]
        })

    elif 'factorial' in methodology:
        config.update({
            "factors": {},
            "response_variable": "conversion_rate"
        })

    # Override with user-provided values
    config.update(kwargs)

    return config


def save_config(config: Dict[str, Any], output_path: str) -> None:
    """
    Save configuration to JSON file.

    Args:
        config: Configuration dictionary
        output_path: Path to save JSON file

    Example:
        >>> config = {'data_path': 'data.csv', 'sample_size': 100}
        >>> save_config(config, 'my_config.json')
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"[SAVED] Configuration saved to: {output_path}")


def print_config(config: Dict[str, Any]) -> None:
    """
    Pretty print configuration dictionary.

    Args:
        config: Configuration dictionary to display
    """
    print("\n" + "="*60)
    print("CONFIGURATION")
    print("="*60)

    for key, value in config.items():
        if isinstance(value, (list, dict)) and len(str(value)) > 50:
            print(f"{key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"  {k}: {v}")
            else:
                for item in value:
                    print(f"  - {item}")
        else:
            print(f"{key}: {value}")

    print("="*60 + "\n")


# Example usage
if __name__ == "__main__":
    # Example 1: Create and save a default config
    print("Example 1: Create default configuration")
    config = create_default_config(
        methodology="simple_random_sampling",
        data_path="data/raw/ecommerce_data.csv",
        sample_size=1000,
        random_seed=42
    )
    print_config(config)

    # Example 2: Validate configuration
    print("\nExample 2: Validate configuration")
    required = ['methodology', 'data_path', 'sample_size']
    optional = {'random_seed': 42, 'output_path': None}

    try:
        validated = validate_config(config, required, optional)
        print("[OK] Configuration validated successfully")
    except ConfigError as e:
        print(f"[ERROR] {e}")

    # Example 3: Save configuration
    print("\nExample 3: Save configuration")
    save_config(config, 'config/example_config.json')
