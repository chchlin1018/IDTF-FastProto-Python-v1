"""
UUIDv7 ID Generator

This module provides UUIDv7 generation functionality for asset_id and tag_id.
UUIDv7 provides time-ordering and distributed-system-friendly unique identifiers.
"""

import time
import uuid
from typing import Optional


def generate_uuidv7() -> str:
    """
    Generate a UUIDv7 string.
    
    UUIDv7 format:
    - 48 bits: Unix timestamp in milliseconds
    - 12 bits: Random bits for sub-millisecond ordering
    - 2 bits: Version (0b111 for v7)
    - 62 bits: Random bits
    
    Returns:
        str: UUIDv7 string in standard format (e.g., "018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f")
    
    Example:
        >>> asset_id = generate_uuidv7()
        >>> print(asset_id)
        018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f
    """
    # Get current timestamp in milliseconds
    timestamp_ms = int(time.time() * 1000)
    
    # Generate random bits
    random_bits = uuid.uuid4().int
    
    # Construct UUIDv7
    # 48 bits: timestamp
    uuid_int = (timestamp_ms & 0xFFFFFFFFFFFF) << 80
    
    # 4 bits: version (0111 = 7)
    uuid_int |= (0x7 << 76)
    
    # 12 bits: random (sub-millisecond ordering)
    uuid_int |= ((random_bits >> 52) & 0xFFF) << 64
    
    # 2 bits: variant (10)
    uuid_int |= (0x2 << 62)
    
    # 62 bits: random
    uuid_int |= random_bits & 0x3FFFFFFFFFFFFFFF
    
    # Convert to UUID object and format as string
    return str(uuid.UUID(int=uuid_int))


def generate_asset_id() -> str:
    """
    Generate an asset_id using UUIDv7.
    
    Returns:
        str: Asset ID in UUIDv7 format
    
    Example:
        >>> asset_id = generate_asset_id()
        >>> print(asset_id)
        018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f
    """
    return generate_uuidv7()


def generate_tag_id() -> str:
    """
    Generate a tag_id using UUIDv7.
    
    Returns:
        str: Tag ID in UUIDv7 format
    
    Example:
        >>> tag_id = generate_tag_id()
        >>> print(tag_id)
        018c3f7e-9b3c-7d4e-8f5a-6b7c8d9e0f1a
    """
    return generate_uuidv7()


def is_valid_uuidv7(uuid_str: str) -> bool:
    """
    Validate if a string is a valid UUIDv7.
    
    Args:
        uuid_str: UUID string to validate
    
    Returns:
        bool: True if valid UUIDv7, False otherwise
    
    Example:
        >>> is_valid_uuidv7("018c3f7e-8a2b-7c3d-9e4f-5a6b7c8d9e0f")
        True
        >>> is_valid_uuidv7("invalid-uuid")
        False
    """
    try:
        # Parse UUID
        uuid_obj = uuid.UUID(uuid_str)
        
        # Check version (should be 7)
        if uuid_obj.version != 7:
            return False
        
        # Check variant (should be RFC 4122)
        if uuid_obj.variant != uuid.RFC_4122:
            return False
        
        return True
    except (ValueError, AttributeError):
        return False


def extract_timestamp_from_uuidv7(uuid_str: str) -> Optional[int]:
    """
    Extract timestamp (in milliseconds) from a UUIDv7.
    
    Args:
        uuid_str: UUIDv7 string
    
    Returns:
        Optional[int]: Timestamp in milliseconds, or None if invalid
    
    Example:
        >>> uuid_str = generate_uuidv7()
        >>> timestamp_ms = extract_timestamp_from_uuidv7(uuid_str)
        >>> print(timestamp_ms)
        1698765432000
    """
    try:
        uuid_obj = uuid.UUID(uuid_str)
        
        # Extract first 48 bits (timestamp)
        timestamp_ms = uuid_obj.int >> 80
        
        return timestamp_ms
    except (ValueError, AttributeError):
        return None


if __name__ == "__main__":
    # Demo
    print("=== UUIDv7 Generator Demo ===\n")
    
    # Generate asset IDs
    print("Asset IDs:")
    for i in range(3):
        asset_id = generate_asset_id()
        print(f"  {asset_id}")
        time.sleep(0.001)  # Small delay to show time ordering
    
    print()
    
    # Generate tag IDs
    print("Tag IDs:")
    for i in range(3):
        tag_id = generate_tag_id()
        print(f"  {tag_id}")
        time.sleep(0.001)
    
    print()
    
    # Validate UUIDs
    print("Validation:")
    valid_uuid = generate_uuidv7()
    print(f"  {valid_uuid}: {is_valid_uuidv7(valid_uuid)}")
    print(f"  invalid-uuid: {is_valid_uuidv7('invalid-uuid')}")
    
    print()
    
    # Extract timestamp
    print("Timestamp Extraction:")
    uuid_str = generate_uuidv7()
    timestamp_ms = extract_timestamp_from_uuidv7(uuid_str)
    print(f"  UUID: {uuid_str}")
    print(f"  Timestamp (ms): {timestamp_ms}")
    print(f"  Timestamp (s): {timestamp_ms / 1000 if timestamp_ms else None}")

