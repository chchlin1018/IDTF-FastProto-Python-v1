"""
Queue - Abstract interfaces for message queue implementations
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class Queue(ABC):
    """
    Abstract message queue interface.
    
    Provides FIFO (First-In-First-Out) message delivery semantics.
    """
    
    @abstractmethod
    def put(self, message: Dict[str, Any]) -> None:
        """
        Put a message into the queue.
        
        Args:
            message: Message dictionary to enqueue
        """
        pass
    
    @abstractmethod
    def get(self, timeout: Optional[float] = None) -> Optional[Dict[str, Any]]:
        """
        Get a message from the queue.
        
        Args:
            timeout: Maximum time to wait for a message (seconds)
                    None means wait indefinitely
                    0 means non-blocking
        
        Returns:
            Message dictionary, or None if timeout expires
        """
        pass
    
    @abstractmethod
    def size(self) -> int:
        """
        Get the current queue size.
        
        Returns:
            Number of messages in the queue
        """
        pass
    
    @abstractmethod
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get message history (for debugging/testing).
        
        Returns:
            List of all messages that have been enqueued
        """
        pass


class QueueManager(ABC):
    """
    Abstract queue manager interface.
    
    Manages multiple named queues.
    """
    
    @abstractmethod
    def get_queue(self, name: str) -> Queue:
        """
        Get or create a queue by name.
        
        Args:
            name: Queue name
        
        Returns:
            Queue instance
        """
        pass
    
    @abstractmethod
    def delete_queue(self, name: str) -> None:
        """
        Delete a queue by name.
        
        Args:
            name: Queue name
        """
        pass
    
    @abstractmethod
    def list_queues(self) -> List[str]:
        """
        List all queue names.
        
        Returns:
            List of queue names
        """
        pass

