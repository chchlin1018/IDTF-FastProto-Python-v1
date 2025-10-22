"""
TSDB - Abstract interfaces for time-series database implementations
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class AggregationFunction(Enum):
    """Aggregation functions for time-series data."""
    AVG = "avg"
    MIN = "min"
    MAX = "max"
    SUM = "sum"
    COUNT = "count"
    FIRST = "first"
    LAST = "last"
    STDDEV = "stddev"


@dataclass
class TagValue:
    """
    Time-series tag value.
    
    Attributes:
        tag_id: Tag identifier (UUIDv7)
        timestamp: Timestamp (ISO 8601 format)
        value: Tag value (numeric or string)
        quality: Data quality indicator (0-100, 100 = good)
        source: Source of the value (e.g., "PLC_001")
    """
    tag_id: str
    timestamp: str
    value: Any
    quality: int = 100
    source: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tag_id": self.tag_id,
            "timestamp": self.timestamp,
            "value": self.value,
            "quality": self.quality,
            "source": self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TagValue":
        """Create from dictionary."""
        return cls(
            tag_id=data["tag_id"],
            timestamp=data["timestamp"],
            value=data["value"],
            quality=data.get("quality", 100),
            source=data.get("source", "")
        )


@dataclass
class AggregatedValue:
    """
    Aggregated time-series value.
    
    Attributes:
        tag_id: Tag identifier
        start_time: Start of aggregation window
        end_time: End of aggregation window
        function: Aggregation function used
        value: Aggregated value
        count: Number of data points in aggregation
    """
    tag_id: str
    start_time: str
    end_time: str
    function: AggregationFunction
    value: Any
    count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tag_id": self.tag_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "function": self.function.value,
            "value": self.value,
            "count": self.count
        }


class ITSDB(ABC):
    """
    Abstract Time-Series Database interface.
    
    Defines the contract for all TSDB implementations.
    """
    
    @abstractmethod
    def write_tag_value(self, tag_value: TagValue) -> bool:
        """
        Write a single tag value.
        
        Args:
            tag_value: Tag value to write
        
        Returns:
            bool: True if written successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def write_tag_values(self, tag_values: List[TagValue]) -> int:
        """
        Write multiple tag values (batch write).
        
        Args:
            tag_values: List of tag values to write
        
        Returns:
            int: Number of values written successfully
        """
        pass
    
    @abstractmethod
    def query_tag_values(
        self,
        tag_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[TagValue]:
        """
        Query tag values within a time range.
        
        Args:
            tag_id: Tag identifier
            start_time: Start time (optional)
            end_time: End time (optional)
            limit: Maximum number of values to return
        
        Returns:
            List[TagValue]: List of tag values
        """
        pass
    
    @abstractmethod
    def query_latest_value(self, tag_id: str) -> Optional[TagValue]:
        """
        Query the latest value for a tag.
        
        Args:
            tag_id: Tag identifier
        
        Returns:
            Optional[TagValue]: Latest tag value, or None if not found
        """
        pass
    
    @abstractmethod
    def query_aggregated_values(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: datetime,
        function: AggregationFunction,
        interval_seconds: int
    ) -> List[AggregatedValue]:
        """
        Query aggregated tag values.
        
        Args:
            tag_id: Tag identifier
            start_time: Start time
            end_time: End time
            function: Aggregation function
            interval_seconds: Aggregation interval in seconds
        
        Returns:
            List[AggregatedValue]: List of aggregated values
        """
        pass
    
    @abstractmethod
    def delete_tag_values(
        self,
        tag_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Delete tag values within a time range.
        
        Args:
            tag_id: Tag identifier
            start_time: Start time (optional, if None, delete from beginning)
            end_time: End time (optional, if None, delete to end)
        
        Returns:
            int: Number of values deleted
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get TSDB statistics.
        
        Returns:
            Dict[str, Any]: Statistics (e.g., total tags, total values, etc.)
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close the TSDB connection and release resources."""
        pass


if __name__ == '__main__':
    from datetime import datetime
    from ..tags.id_generator import generate_uuidv7
    
    print("=== TSDB Interfaces Demo ===\n")
    
    # Create a sample tag value
    print("--- Creating Sample Tag Value ---")
    tag_value = TagValue(
        tag_id=generate_uuidv7(),
        timestamp=datetime.utcnow().isoformat() + "Z",
        value=25.5,
        quality=100,
        source="PLC_001"
    )
    
    print(f"Tag ID: {tag_value.tag_id}")
    print(f"Timestamp: {tag_value.timestamp}")
    print(f"Value: {tag_value.value}")
    print(f"Quality: {tag_value.quality}")
    print(f"Source: {tag_value.source}")
    print()
    
    # Convert to dict and back
    print("--- Tag Value Serialization ---")
    tag_value_dict = tag_value.to_dict()
    print(f"Tag value as dict: {tag_value_dict}")
    
    reconstructed_tag_value = TagValue.from_dict(tag_value_dict)
    print(f"Reconstructed tag ID: {reconstructed_tag_value.tag_id}")
    print()
    
    # Aggregation functions
    print("--- Aggregation Functions ---")
    for func in AggregationFunction:
        print(f"- {func.name}: {func.value}")
    print()
    
    # Create a sample aggregated value
    print("--- Creating Sample Aggregated Value ---")
    agg_value = AggregatedValue(
        tag_id=tag_value.tag_id,
        start_time=datetime.utcnow().isoformat() + "Z",
        end_time=datetime.utcnow().isoformat() + "Z",
        function=AggregationFunction.AVG,
        value=25.5,
        count=10
    )
    
    print(f"Aggregated Value: {agg_value.to_dict()}")
    print()
    
    print("Note: ITSDB is an abstract interface.")
    print("Concrete implementations (SQLiteTSDB, DuckDBTSDB, TDEngineTSDB)")
    print("will be provided in separate modules.")

