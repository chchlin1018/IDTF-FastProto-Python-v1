"""
IO - CSV utilities for reading and writing CSV files
"""

import csv
from pathlib import Path
from typing import List, Dict, Any, Union, Optional


def read_csv(
    file_path: Union[str, Path],
    delimiter: str = ',',
    skip_header: bool = False
) -> List[List[str]]:
    """
    Read a CSV file and return its content as a list of lists.
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter (default: ',')
        skip_header: Whether to skip the first row (default: False)
    
    Returns:
        List[List[str]]: List of rows, each row is a list of strings
    
    Raises:
        FileNotFoundError: If the file does not exist
    
    Example:
        >>> rows = read_csv("data.csv")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    rows = []
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f, delimiter=delimiter)
        
        if skip_header:
            next(reader, None)  # Skip header row
        
        for row in reader:
            rows.append(row)
    
    return rows


def write_csv(
    data: List[List[Any]],
    file_path: Union[str, Path],
    delimiter: str = ',',
    header: Optional[List[str]] = None
):
    """
    Write data to a CSV file.
    
    Args:
        data: List of rows to write
        file_path: Path to the output CSV file
        delimiter: CSV delimiter (default: ',')
        header: Optional header row
    
    Example:
        >>> data = [["John", 30], ["Jane", 25]]
        >>> write_csv(data, "output.csv", header=["Name", "Age"])
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter)
        
        if header:
            writer.writerow(header)
        
        writer.writerows(data)


def read_csv_as_dicts(
    file_path: Union[str, Path],
    delimiter: str = ','
) -> List[Dict[str, str]]:
    """
    Read a CSV file with headers and return as a list of dictionaries.
    
    Args:
        file_path: Path to the CSV file
        delimiter: CSV delimiter (default: ',')
    
    Returns:
        List[Dict[str, str]]: List of dictionaries, one per row
    
    Example:
        >>> records = read_csv_as_dicts("data.csv")
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"CSV file not found: {file_path}")
    
    records = []
    with open(file_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f, delimiter=delimiter)
        for row in reader:
            records.append(dict(row))
    
    return records


def write_csv_from_dicts(
    data: List[Dict[str, Any]],
    file_path: Union[str, Path],
    fieldnames: Optional[List[str]] = None,
    delimiter: str = ','
):
    """
    Write a list of dictionaries to a CSV file.
    
    Args:
        data: List of dictionaries to write
        file_path: Path to the output CSV file
        fieldnames: Optional list of field names (default: keys from first dict)
        delimiter: CSV delimiter (default: ',')
    
    Example:
        >>> data = [{"name": "John", "age": 30}, {"name": "Jane", "age": 25}]
        >>> write_csv_from_dicts(data, "output.csv")
    """
    if not data:
        return
    
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    if fieldnames is None:
        fieldnames = list(data[0].keys())
    
    with open(file_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(data)


def append_csv_row(
    row: List[Any],
    file_path: Union[str, Path],
    delimiter: str = ','
):
    """
    Append a single row to a CSV file.
    
    Args:
        row: Row data to append
        file_path: Path to the CSV file
        delimiter: CSV delimiter (default: ',')
    
    Example:
        >>> append_csv_row(["John", 30], "data.csv")
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=delimiter)
        writer.writerow(row)


if __name__ == '__main__':
    import tempfile
    
    print("=== CSV Utilities Demo ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Write CSV with header
        print("--- Writing CSV ---")
        data = [
            ["John", 30, "Engineer"],
            ["Jane", 25, "Designer"],
            ["Bob", 35, "Manager"]
        ]
        header = ["Name", "Age", "Role"]
        
        csv_file = temp_dir_path / "employees.csv"
        write_csv(data, csv_file, header=header)
        print(f"Written to: {csv_file}")
        print()
        
        # Read CSV
        print("--- Reading CSV ---")
        rows = read_csv(csv_file)
        print(f"Read {len(rows)} rows:")
        for row in rows:
            print(f"  {row}")
        print()
        
        # Read CSV as dictionaries
        print("--- Reading CSV as Dictionaries ---")
        records = read_csv_as_dicts(csv_file)
        print(f"Read {len(records)} records:")
        for record in records:
            print(f"  {record}")
        print()
        
        # Write CSV from dictionaries
        print("--- Writing CSV from Dictionaries ---")
        dict_data = [
            {"asset_id": "001", "name": "Pump A", "status": "Running"},
            {"asset_id": "002", "name": "Pump B", "status": "Stopped"},
            {"asset_id": "003", "name": "Pump C", "status": "Running"}
        ]
        
        assets_file = temp_dir_path / "assets.csv"
        write_csv_from_dicts(dict_data, assets_file)
        print(f"Written to: {assets_file}")
        print()
        
        # Append row
        print("--- Appending Row ---")
        append_csv_row(["Alice", 28, "Developer"], csv_file)
        print(f"Appended row to: {csv_file}")
        
        updated_rows = read_csv(csv_file)
        print(f"Updated CSV has {len(updated_rows)} rows")
        print()
        
        print("Demo completed.")

