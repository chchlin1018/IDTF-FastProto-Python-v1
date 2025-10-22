"""
IADL Parser - Parse YAML/JSON to Asset model
"""

import yaml
import json
from pathlib import Path
from typing import Union
from .models import Asset


def parse_iadl_file(file_path: Union[str, Path]) -> Asset:
    """
    Parse IADL file (YAML or JSON) to Asset model.
    
    Args:
        file_path: Path to IADL file
    
    Returns:
        Asset: Parsed asset
    
    Example:
        >>> # Assuming 'pump_001.yaml' exists in testfiles/IADL
        >>> # from pathlib import Path
        >>> # from src.core.iadl.parser import parse_iadl_file
        >>> # asset = parse_iadl_file(Path("testfiles/IADL/schneider_ups.yaml"))
        >>> # print(asset.name)
        # Centrifugal Pump Model A
    """
    file_path = Path(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        elif file_path.suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    return Asset.from_dict(data)


def parse_iadl_string(content: str, format: str = 'yaml') -> Asset:
    """
    Parse IADL string (YAML or JSON) to Asset model.
    
    Args:
        content: IADL content as string
        format: Format of the content ('yaml' or 'json')
    
    Returns:
        Asset: Parsed asset
    
    Example:
        from src.core.iadl.parser import parse_iadl_string
        yaml_content = 'asset_id: 123...'
        asset = parse_iadl_string(yaml_content, format='yaml')
        print(asset.name)
    """
    if format == 'yaml':
        data = yaml.safe_load(content)
    elif format == 'json':
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return Asset.from_dict(data)


def write_iadl_file(asset: Asset, file_path: Union[str, Path], format: str = 'yaml'):
    """
    Write Asset model to IADL file (YAML or JSON).
    
    Args:
        asset: Asset model to write
        file_path: Path to output file
        format: Output format ('yaml' or 'json')
    
    Example:
        >>> # from src.core.iadl.parser import write_iadl_file
        >>> # from src.core.iadl.models import Asset, Units, Transform, Metadata
        >>> # from src.core.tags.id_generator import generate_asset_id
        >>> # asset = Asset(asset_id=generate_asset_id(), name="Test", model_ref="path")
        >>> # write_iadl_file(asset, "output_asset.yaml")
    """
    file_path = Path(file_path)
    data = asset.to_dict()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if format == 'yaml':
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        elif format == 'json':
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == '__main__':
    from pathlib import Path
    from src.core.tags.id_generator import generate_asset_id
    from src.core.iadl.models import Asset, Units, Transform, Metadata
    
    # Create a dummy asset for testing write_iadl_file
    test_asset = Asset(
        asset_id=generate_asset_id(),
        name="Test Asset for Parser",
        description="A simple asset for demonstrating IADL parser functionality.",
        model_ref="@/test/model.usd@</TestModel>",
        units=Units(length="m"),
        default_xform=Transform(translation=[1.0, 2.0, 3.0]),
        metadata=Metadata(author="Parser Test", version="0.1.0")
    )
    
    # Write to YAML
    yaml_output_path = Path("test_output_asset.yaml")
    write_iadl_file(test_asset, yaml_output_path, format='yaml')
    print(f"Wrote test asset to {yaml_output_path}")
    
    # Read from YAML
    parsed_asset_yaml = parse_iadl_file(yaml_output_path)
    print(f"Parsed asset name from YAML: {parsed_asset_yaml.name}")
    
    # Write to JSON
    json_output_path = Path("test_output_asset.json")
    write_iadl_file(test_asset, json_output_path, format='json')
    print(f"Wrote test asset to {json_output_path}")
    
    # Read from JSON
    parsed_asset_json = parse_iadl_file(json_output_path)
    print(f"Parsed asset name from JSON: {parsed_asset_json.name}")
    
    # Clean up test files
    yaml_output_path.unlink()
    json_output_path.unlink()
    print("Cleaned up test files.")

    # Example using a test file from testfiles/IADL
    test_file_path = Path("testfiles/IADL/schneider_ups.yaml")
    if test_file_path.exists():
        print(f"\nParsing existing IADL file: {test_file_path}")
        schneider_ups_asset = parse_iadl_file(test_file_path)
        print(f"Asset ID: {schneider_ups_asset.asset_id}")
        print(f"Asset Name: {schneider_ups_asset.name}")
        print(f"Model Ref: {schneider_ups_asset.model_ref}")
        if schneider_ups_asset.tags:
            print(f"First Tag Name: {schneider_ups_asset.tags[0].name}")
    else:
        print(f"\nTest file not found: {test_file_path}. Please ensure it exists.")

