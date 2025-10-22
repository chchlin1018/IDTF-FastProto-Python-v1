"""
IO - JSON utilities for reading and writing JSON files
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union


def read_json(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Read a JSON file and return its content as a dictionary.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        Dict[str, Any]: Parsed JSON content
    
    Raises:
        FileNotFoundError: If the file does not exist
        json.JSONDecodeError: If the file is not valid JSON
    
    Example:
        >>> data = read_json("config.json")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def write_json(
    data: Dict[str, Any],
    file_path: Union[str, Path],
    indent: int = 2,
    sort_keys: bool = False
):
    """
    Write a dictionary to a JSON file.
    
    Args:
        data: Dictionary to write
        file_path: Path to the output JSON file
        indent: Indentation level (default: 2)
        sort_keys: Whether to sort keys alphabetically (default: False)
    
    Example:
        >>> data = {"name": "Test", "value": 42}
        >>> write_json(data, "output.json")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, sort_keys=sort_keys, ensure_ascii=False)


def read_json_list(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """
    Read a JSON file containing a list of dictionaries.
    
    Args:
        file_path: Path to the JSON file
    
    Returns:
        List[Dict[str, Any]]: List of parsed JSON objects
    
    Example:
        >>> items = read_json_list("items.json")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"JSON file not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
        if not isinstance(data, list):
            raise ValueError(f"Expected a list in JSON file, got {type(data).__name__}")
        
        return data


def write_json_list(
    data: List[Dict[str, Any]],
    file_path: Union[str, Path],
    indent: int = 2
):
    """
    Write a list of dictionaries to a JSON file.
    
    Args:
        data: List of dictionaries to write
        file_path: Path to the output JSON file
        indent: Indentation level (default: 2)
    
    Example:
        >>> items = [{"name": "Item1"}, {"name": "Item2"}]
        >>> write_json_list(items, "items.json")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def merge_json_files(file_paths: List[Union[str, Path]]) -> Dict[str, Any]:
    """
    Merge multiple JSON files into a single dictionary.
    Later files override earlier ones for conflicting keys.
    
    Args:
        file_paths: List of JSON file paths to merge
    
    Returns:
        Dict[str, Any]: Merged dictionary
    
    Example:
        >>> merged = merge_json_files(["base.json", "override.json"])
    """
    merged = {}
    
    for file_path in file_paths:
        data = read_json(file_path)
        merged.update(data)
    
    return merged


def pretty_print_json(data: Dict[str, Any], indent: int = 2):
    """
    Pretty print a dictionary as JSON to console.
    
    Args:
        data: Dictionary to print
        indent: Indentation level (default: 2)
    
    Example:
        >>> pretty_print_json({"name": "Test", "value": 42})
    """
    print(json.dumps(data, indent=indent, ensure_ascii=False))


if __name__ == '__main__':
    import tempfile
    
    print("=== JSON Utilities Demo ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Write JSON
        print("--- Writing JSON ---")
        data = {
            "name": "Test Asset",
            "type": "Pump",
            "properties": {
                "flow_rate": 100.0,
                "pressure": 5.0
            },
            "tags": ["production", "critical"]
        }
        
        json_file = temp_dir_path / "test.json"
        write_json(data, json_file)
        print(f"Written to: {json_file}")
        print()
        
        # Read JSON
        print("--- Reading JSON ---")
        read_data = read_json(json_file)
        print(f"Read data:")
        pretty_print_json(read_data)
        print()
        
        # Write JSON list
        print("--- Writing JSON List ---")
        items = [
            {"id": 1, "name": "Item 1"},
            {"id": 2, "name": "Item 2"},
            {"id": 3, "name": "Item 3"}
        ]
        
        list_file = temp_dir_path / "items.json"
        write_json_list(items, list_file)
        print(f"Written list to: {list_file}")
        print()
        
        # Read JSON list
        print("--- Reading JSON List ---")
        read_items = read_json_list(list_file)
        print(f"Read {len(read_items)} items:")
        for item in read_items:
            print(f"  - {item}")
        print()
        
        # Merge JSON files
        print("--- Merging JSON Files ---")
        base_file = temp_dir_path / "base.json"
        override_file = temp_dir_path / "override.json"
        
        write_json({"a": 1, "b": 2, "c": 3}, base_file)
        write_json({"b": 20, "d": 4}, override_file)
        
        merged = merge_json_files([base_file, override_file])
        print(f"Merged data:")
        pretty_print_json(merged)
        print()
        
        print("Demo completed.")

