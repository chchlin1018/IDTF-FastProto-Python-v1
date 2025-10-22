"""
FDL Parser - Parse YAML/JSON to FDL model
"""

import yaml
import json
from pathlib import Path
from typing import Union
from .models import FDL


def parse_fdl_file(file_path: Union[str, Path]) -> FDL:
    """
    Parse FDL file (YAML or JSON) to FDL model.
    
    Args:
        file_path: Path to FDL file
    
    Returns:
        FDL: Parsed FDL object
    
    Example:
        >>> # Assuming 'semiconductor_fab.yaml' exists in testfiles/FDL
        >>> # from pathlib import Path
        >>> # from src.core.fdl.parser import parse_fdl_file
        >>> # fdl_obj = parse_fdl_file(Path("testfiles/FDL/semiconductor_fab.yaml"))
        >>> # print(fdl_obj.site.name)
        # Semiconductor Fab 1
    """
    file_path = Path(file_path)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        if file_path.suffix in ['.yaml', '.yml']:
            data = yaml.safe_load(f)
        elif file_path.suffix == '.json':
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    return FDL.from_dict(data)


def parse_fdl_string(content: str, format: str = 'yaml') -> FDL:
    """
    Parse FDL string (YAML or JSON) to FDL model.
    
    Args:
        content: FDL content as string
        format: Format of the content ('yaml' or 'json')
    
    Returns:
        FDL: Parsed FDL object
    """
    if format == 'yaml':
        data = yaml.safe_load(content)
    elif format == 'json':
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported format: {format}")
    
    return FDL.from_dict(data)


def write_fdl_file(fdl_obj: FDL, file_path: Union[str, Path], format: str = 'yaml'):
    """
    Write FDL model to FDL file (YAML or JSON).
    
    Args:
        fdl_obj: FDL model to write
        file_path: Path to output file
        format: Output format ('yaml' or 'json')
    """
    file_path = Path(file_path)
    data = fdl_obj.to_dict()
    
    with open(file_path, 'w', encoding='utf-8') as f:
        if format == 'yaml':
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        elif format == 'json':
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")


if __name__ == '__main__':
    from pathlib import Path
    from src.core.tags.id_generator import generate_uuidv7
    from src.core.iadl.models import Transform
    from src.core.fdl.models import FDL, Site, Area, AssetInstance, Connection, GlobalConstraints, ScalingConstraints, CollisionDetection, BatchLayout

    # Create a dummy FDL object for testing write_fdl_file
    test_fdl = FDL(
        site=Site(
            name="Test Site",
            site_id=generate_uuidv7(),
            areas=[
                Area(
                    name="Test Area",
                    area_id=generate_uuidv7(),
                    instances=[
                        AssetInstance(
                            instance_id="test_asset_001",
                            ref_asset=generate_uuidv7(),
                            transform=Transform(translation=[1.0, 1.0, 0.0])
                        )
                    ]
                )
            ]
        ),
        global_constraints=GlobalConstraints(
            scaling_constraints=ScalingConstraints(allow_scaling=False),
            collision_detection=CollisionDetection(enabled=True, clearance_distance=0.1)
        ),
        batch_layouts=[
            BatchLayout(
                layout_id="test_grid",
                type="grid",
                ref_asset=generate_uuidv7(),
                params={
                    "rows": 2,
                    "columns": 2,
                    "spacing_x": 5.0,
                    "spacing_y": 5.0,
                    "origin": [0.0, 0.0, 0.0]
                }
            )
        ]
    )

    # Write to YAML
    yaml_output_path = Path("test_output_fdl.yaml")
    write_fdl_file(test_fdl, yaml_output_path, format='yaml')
    print(f"Wrote test FDL to {yaml_output_path}")

    # Read from YAML
    parsed_fdl_yaml = parse_fdl_file(yaml_output_path)
    print(f"Parsed FDL site name from YAML: {parsed_fdl_yaml.site.name}")

    # Write to JSON
    json_output_path = Path("test_output_fdl.json")
    write_fdl_file(test_fdl, json_output_path, format='json')
    print(f"Wrote test FDL to {json_output_path}")

    # Read from JSON
    parsed_fdl_json = parse_fdl_file(json_output_path)
    print(f"Parsed FDL site name from JSON: {parsed_fdl_json.site.name}")

    # Clean up test files
    yaml_output_path.unlink()
    json_output_path.unlink()
    print("Cleaned up test files.")

    # Example using a test file from testfiles/FDL
    test_file_path = Path("testfiles/FDL/semiconductor_fab.yaml")
    if test_file_path.exists():
        print(f"\nParsing existing FDL file: {test_file_path}")
        semiconductor_fab_fdl = parse_fdl_file(test_file_path)
        print(f"Site Name: {semiconductor_fab_fdl.site.name}")
        print(f"First Area: {semiconductor_fab_fdl.site.areas[0].name}")
        print(f"Global Constraints - Allow Scaling: {semiconductor_fab_fdl.global_constraints.scaling_constraints.allow_scaling}")
        print(f"Batch Layouts: {len(semiconductor_fab_fdl.batch_layouts)}")
    else:
        print(f"\nTest file not found: {test_file_path}. Please ensure it exists.")

