"""
IO - YAML utilities for reading and writing YAML files
"""

import yaml
from pathlib import Path
from typing import Any, Dict, List, Union


def read_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read a YAML file and return its content as a dictionary.
    
    Args:
        file_path: Path to the YAML file
    
    Returns:
        Dict[str, Any]: Parsed YAML content
    
    Raises:
        FileNotFoundError: If the file does not exist
        yaml.YAMLError: If the file is not valid YAML
    
    Example:
        >>> data = read_yaml("config.yaml")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def write_yaml(data: Dict[str, Any], file_path: Union[str, Path], sort_keys: bool = False):
    """
    Write a dictionary to a YAML file.
    
    Args:
        data: Dictionary to write
        file_path: Path to the output YAML file
        sort_keys: Whether to sort keys alphabetically (default: False)
    
    Example:
        >>> data = {"name": "Test", "value": 42}
        >>> write_yaml(data, "output.yaml")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=sort_keys, allow_unicode=True)


def read_yaml_list(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Read a YAML file containing a list of dictionaries.
    
    Args:
        file_path: Path to the YAML file
    
    Returns:
        List[Dict[str, Any]]: List of parsed YAML objects
    
    Example:
        >>> items = read_yaml_list("items.yaml")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"YAML file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
        
        if not isinstance(data, list):
            raise ValueError(f"Expected a list in YAML file, got {type(data).__name__}")
        
        return data


def write_yaml_list(data: List[Dict[str, Any]], file_path: Union[str, Path]):
    """
    Write a list of dictionaries to a YAML file.
    
    Args:
        data: List of dictionaries to write
        file_path: Path to the output YAML file
    
    Example:
        >>> items = [{"name": "Item1"}, {"name": "Item2"}]
        >>> write_yaml_list(items, "items.yaml")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True)


def merge_yaml_files(file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
    """
    Merge multiple YAML files into a single dictionary.
    Later files override earlier ones for conflicting keys.
    
    Args:
        file_paths: List of YAML file paths to merge
    
    Returns:
        Dict[str, Any]: Merged dictionary
    
    Example:
        >>> merged = merge_yaml_files(["base.yaml", "override.yaml"])
    """
    merged = {}
    
    for file_path in file_paths:
        data = read_yaml(file_path)
        merged.update(data)
    
    return merged


if __name__ == '__main__':
    import tempfile
    import os
    
    print("=== YAML Utilities Demo ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Write YAML
        print("--- Writing YAML ---")
        data = {
            "name": "Test Asset",
            "type": "Pump",
            "properties": {
                "flow_rate": 100.0,
                "pressure": 5.0
            },
            "tags": ["production", "critical"]
        }
        
        yaml_file = temp_dir_path / "test.yaml"
        write_yaml(data, yaml_file)
        print(f"Written to: {yaml_file}")
        print()
        
        # Read YAML
        print("--- Reading YAML ---")
        read_data = read_yaml(yaml_file)
        print(f"Read data: {read_data}")
        print()
        
        # Write YAML list
        print("--- Writing YAML List ---")
        items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
        
        list_file = temp_dir_path / "items.yaml"
        write_yaml_list(items, list_file)
        print(f"Written list to: {list_file}")
        print()
        
        # Read YAML list
        print("--- Reading YAML List ---")
        read_items = read_yaml_list(list_file)
        print(f"Read {len(read_items)} items")
        for item in read_items:
            print(f"  - {item}")
        print()
        
        # Merge YAML files
        print("--- Merging YAML Files ---")
        base_file = temp_dir_path / "base.yaml"
        override_file = temp_dir_path / "override.yaml"
        
        write_yaml({"a": 1, "b": 2, "c": 3}, base_file)
        write_yaml({"b": 20, "d": 4}, override_file)
        
        merged = merge_yaml_files([base_file, override_file])
        print(f"Merged data: {merged}")
        print()
        
        print("Demo completed.")

