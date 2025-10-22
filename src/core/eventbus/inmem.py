"""
Event Bus - In-Memory implementation (for MVP and testing)
"""

from typing import Callable, List, Dict, Any, Optional
from datetime import datetime
from threading import Lock
import uuid

from .interfaces import IEventBus, Event, DeliveryGuarantee


class InMemoryEventBus(IEventBus):
    """
    In-memory event bus implementation.
    
    Suitable for MVP, single-process applications, and testing.
    Events are stored in memory and lost when the process terminates.
    """
    
    def __init__(self, max_history_size: int = 10000):
        """
        Initialize in-memory event bus.
        
        Args:
            max_history_size: Maximum number of events to keep in history
        """
        self.max_history_size = max_history_size
        self.event_history: List[Event] = []
        self.subscriptions: Dict[str, Dict[str, Any]] = {}  # subscription_id -> {event_type, callback, filter_func}
        self.lock = Lock()
        self.stats = {
            "total_published": 0,
            "total_delivered": 0,
            "total_subscriptions": 0
        }
    
    def publish(
        self,
        event: Event,
        guarantee: DeliveryGuarantee = DeliveryGuarantee.AT_LEAST_ONCE
    ) -> bool:
        """Publish an event to the bus."""
        with self.lock:
            # Add to history
            self.event_history.append(event)
            if len(self.event_history) > self.max_history_size:
                self.event_history.pop(0)
            
            self.stats["total_published"] += 1
            
            # Deliver to subscribers
            for sub_id, sub_info in self.subscriptions.items():
                if sub_info["event_type"] == event.event_type or sub_info["event_type"] == "*":
                    # Apply filter if provided
                    if sub_info["filter_func"] is not None:
                        if not sub_info["filter_func"](event):
                            continue
                    
                    # Call callback
                    try:
                        sub_info["callback"](event)
                        self.stats["total_delivered"] += 1
                    except Exception as e:
                        print(f"Error in event callback for subscription {sub_id}: {e}")
            
            return True
    
    def subscribe(
        self,
        event_type: str,
        callback: Callable[[Event], None],
        filter_func: Optional[Callable[[Event], bool]] = None
    ) -> str:
        """Subscribe to events of a specific type."""
        subscription_id = str(uuid.uuid4())
        
        with self.lock:
            self.subscriptions[subscription_id] = {
                "event_type": event_type,
                "callback": callback,
                "filter_func": filter_func
            }
            self.stats["total_subscriptions"] += 1
        
        return subscription_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        with self.lock:
            if subscription_id in self.subscriptions:
                del self.subscriptions[subscription_id]
                return True
            return False
    
    def get_event_history(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Event]:
        """Get historical events."""
        with self.lock:
            filtered_events = self.event_history.copy()
            
            # Filter by event type
            if event_type:
                filtered_events = [e for e in filtered_events if e.event_type == event_type]
            
            # Filter by time range
            if start_time:
                start_time_str = start_time.isoformat() + "Z"
                filtered_events = [e for e in filtered_events if e.timestamp >= start_time_str]
            
            if end_time:
                end_time_str = end_time.isoformat() + "Z"
                filtered_events = [e for e in filtered_events if e.timestamp <= end_time_str]
            
            # Apply limit
            return filtered_events[-limit:]
    
    def replay_events(
        self,
        event_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """Replay historical events to current subscribers."""
        events_to_replay = self.get_event_history(event_type, start_time, end_time, limit=self.max_history_size)
        
        for event in events_to_replay:
            # Re-publish without adding to history again
            with self.lock:
                for sub_id, sub_info in self.subscriptions.items():
                    if sub_info["event_type"] == event.event_type or sub_info["event_type"] == "*":
                        if sub_info["filter_func"] is not None:
                            if not sub_info["filter_func"](event):
                                continue
                        
                        try:
                            sub_info["callback"](event)
                        except Exception as e:
                            print(f"Error in event replay callback for subscription {sub_id}: {e}")
    
    def clear_history(self):
        """Clear all event history."""
        with self.lock:
            self.event_history.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        with self.lock:
            return {
                **self.stats,
                "current_history_size": len(self.event_history),
                "active_subscriptions": len(self.subscriptions)
            }


if __name__ == '__main__':
    from datetime import datetime
    from ..tags.id_generator import generate_uuidv7
    import time
    
    print("=== In-Memory Event Bus Demo ===\n")
    
    # Create event bus
    event_bus = InMemoryEventBus(max_history_size=100)
    
    # Create a callback function
    received_events = []
    
    def on_tag_value_changed(event: Event):
        print(f"Received event: {event.event_type} from {event.source}")
        print(f"  Payload: {event.payload}")
        received_events.append(event)
    
    # Subscribe to events
    print("--- Subscribing to Events ---")
    sub_id = event_bus.subscribe("TagValueChanged", on_tag_value_changed)
    print(f"Subscription ID: {sub_id}")
    print()
    
    # Publish events
    print("--- Publishing Events ---")
    for i in range(5):
        event = Event(
            event_id=generate_uuidv7(),
            event_type="TagValueChanged",
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=f"PLC_{i:03d}",
            payload={
                "tag_id": generate_uuidv7(),
                "tag_name": f"Temperature_{i}",
                "value": 20.0 + i,
                "unit": "°C"
            }
        )
        event_bus.publish(event)
        time.sleep(0.1)
    
    print(f"\nReceived {len(received_events)} events via callback")
    print()
    
    # Get event history
    print("--- Event History ---")
    history = event_bus.get_event_history(event_type="TagValueChanged", limit=10)
    print(f"History contains {len(history)} events")
    for event in history[:3]:
        print(f"  - {event.timestamp}: {event.source} -> {event.payload.get('tag_name')}")
    print()
    
    # Get statistics
    print("--- Event Bus Statistics ---")
    stats = event_bus.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Unsubscribe
    print("--- Unsubscribing ---")
    event_bus.unsubscribe(sub_id)
    print(f"Unsubscribed: {sub_id}")
    print()
    
    # Publish after unsubscribe (should not be received)
    print("--- Publishing After Unsubscribe ---")
    event = Event(
        event_id=generate_uuidv7(),
        event_type="TagValueChanged",
        timestamp=datetime.utcnow().isoformat() + "Z",
        source="PLC_999",
        payload={"tag_name": "AfterUnsubscribe", "value": 99.9}
    )
    event_bus.publish(event)
    print(f"Total received events (should still be 5): {len(received_events)}")
    print()
    
    # Replay events
    print("--- Replaying Events ---")
    replayed_events = []
    
    def on_replay(event: Event):
        replayed_events.append(event)
    
    sub_id_replay = event_bus.subscribe("TagValueChanged", on_replay)
    event_bus.replay_events(event_type="TagValueChanged")
    print(f"Replayed {len(replayed_events)} events")
    event_bus.unsubscribe(sub_id_replay)
    print()

