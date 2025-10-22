"""
Event Bus - Abstract interfaces for event bus implementations
"""

from abc import ABC, abstractmethod
from typing import Callable, List, Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class DeliveryGuarantee(Enum):
    """Event delivery guarantee levels."""
    AT_MOST_ONCE = "at_most_once"      # Fire and forget
    AT_LEAST_ONCE = "at_least_once"    # May deliver duplicates
    EXACTLY_ONCE = "exactly_once"       # Guaranteed single delivery


@dataclass
class Event:
    """
    Base event structure.
    
    Attributes:
        event_id: Unique event identifier (UUIDv7)
        event_type: Type of event (e.g., "TagValueChanged", "AlarmRaised")
        timestamp: Event timestamp (ISO 8601 format)
        source: Source of the event (e.g., "PLC_001", "SCADA_System")
        version: Event schema version (semantic versioning)
        payload: Event-specific data
    """
    event_id: str
    event_type: str
    timestamp: str
    source: str
    version: str = "1.0.0"
    payload: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "version": self.version,
            "payload": self.payload or {}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Event":
        """Create event from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=data["event_type"],
            timestamp=data["timestamp"],
            source=data["source"],
            version=data.get("version", "1.0.0"),
            payload=data.get("payload", {})
        )


class IEventBus(ABC):
    """
    Abstract Event Bus interface.
    
    Defines the contract for all event bus implementations.
    """
    
    @abstractmethod
    def publish(
        self,
        event: Event,
        guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    ) -> bool:
        """
        Publish an event to the bus.
        
        Args:
            event: Event to publish
            guarantee: Delivery guarantee level
        
        Returns:
            bool: True if published successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> str:
        """
        Subscribe to events of a specific type.
        
        Args:
            event_type: Type of events to subscribe to (e.g., "TagValueChanged")
            callback: Function to call when an event is received
            filter_func: Optional filter function to apply before calling callback
        
        Returns:
            str: Subscription ID
        """
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: Subscription ID returned by subscribe()
        
        Returns:
            bool: True if unsubscribed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_event_history(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get historical events.
        
        Args:
            event_type: Optional event type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
            limit: Maximum number of events to return
        
        Returns:
            List[Event]: List of historical events
        """
        pass
    
    @abstractmethod
    def replay_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """
        Replay historical events to current subscribers.
        
        Args:
            event_type: Optional event type filter
            start_time: Optional start time filter
            end_time: Optional end time filter
        """
        pass
    
    @abstractmethod
    def clear_history(self):
        """Clear all event history."""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get event bus statistics.
        
        Returns:
            Dict[str, Any]: Statistics (e.g., total events, subscribers, etc.)
        """
        pass


if __name__ == '__main__':
    from datetime import datetime
    from ..tags.id_generator import generate_uuidv7
    
    print("=== Event Bus Interfaces Demo ===\n")
    
    # Create a sample event
    print("--- Creating Sample Event ---")
    event = Event(
        event_id=generate_uuidv7(),
        event_type="TagValueChanged",
        timestamp=datetime.utcnow().isoformat() + "Z",
        source="PLC_001",
        version="1.0.0",
        payload={
            "tag_id": generate_uuidv7(),
            "tag_name": "Temperature",
            "value": 25.5,
            "unit": "°C"
        }
    )
    
    print(f"Event ID: {event.event_id}")
    print(f"Event Type: {event.event_type}")
    print(f"Timestamp: {event.timestamp}")
    print(f"Source: {event.source}")
    print(f"Payload: {event.payload}")
    print()
    
    # Convert to dict and back
    print("--- Event Serialization ---")
    event_dict = event.to_dict()
    print(f"Event as dict: {event_dict}")
    
    reconstructed_event = Event.from_dict(event_dict)
    print(f"Reconstructed event ID: {reconstructed_event.event_id}")
    print()
    
    # Delivery guarantees
    print("--- Delivery Guarantees ---")
    for guarantee in DeliveryGuarantee:
        print(f"- {guarantee.name}: {guarantee.value}")
    print()
    
    print("Note: IEventBus is an abstract interface.")
    print("Concrete implementations (InMemoryEventBus, ZMQEventBus, MQTTEventBus)")
    print("will be provided in separate modules.")

