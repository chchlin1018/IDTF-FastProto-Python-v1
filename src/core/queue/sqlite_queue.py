"""
SQLite Queue - SQLite-based message queue implementation for development
"""

import sqlite3
import json
import time
from typing import Dict, Any, Optional, List
from threading import Lock
from datetime import datetime

from .interfaces import Queue, QueueManager


class SQLiteQueue(Queue):
    """
    SQLite-based message queue implementation.
    
    Features:
    - Persistent storage using SQLite
    - Thread-safe operations
    - Message history tracking
    - FIFO delivery semantics
    
    Attributes:
        name: Queue name
        db_path: Path to SQLite database file
        max_size: Maximum queue size (0 = unlimited)
    """
    
    def __init__(self, name: str, db_path: str = "idtf_queue.db", max_size: int = 10000):
        """
        Initialize SQLite queue.
        
        Args:
            name: Queue name
            db_path: Path to SQLite database file
            max_size: Maximum queue size (0 = unlimited)
        """
        self.name = name
        self.db_path = db_path
        self.max_size = max_size
        self._lock = Lock()
        # Sanitize table name (only allow alphanumeric and underscore)
        self._safe_name = ''.join(c if c.isalnum() or c == '_' else '_' for c in self.name)
        # Create persistent connection
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._init_db()
    
    def _init_db(self) -> None:
        """Initialize database tables."""
        with self._lock:
            # Create messages table
            self._conn.execute(f'''
                CREATE TABLE IF NOT EXISTS queue_{self._safe_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    consumed INTEGER DEFAULT 0
                )
            ''')
            
            # Create history table
            self._conn.execute(f'''
                CREATE TABLE IF NOT EXISTS queue_{self._safe_name}_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self._conn.commit()
    
    def put(self, message: Dict[str, Any]) -> None:
        """
        Put a message into the queue.
        
        Args:
            message: Message dictionary to enqueue
        
        Raises:
            ValueError: If queue is full and max_size > 0
        """
        with self._lock:
            # Check queue size
            if self.max_size > 0:
                cursor = self._conn.execute(
                    f'SELECT COUNT(*) FROM queue_{self._safe_name} WHERE consumed = 0'
                )
                current_size = cursor.fetchone()[0]
                if current_size >= self.max_size:
                    raise ValueError(f"Queue {self.name} is full (max_size={self.max_size})")
            
            # Insert message
            message_json = json.dumps(message)
            self._conn.execute(
                f'INSERT INTO queue_{self._safe_name} (message) VALUES (?)',
                (message_json,)
            )
            
            # Add to history
            self._conn.execute(
                f'INSERT INTO queue_{self._safe_name}_history (message) VALUES (?)',
                (message_json,)
            )
            
            self._conn.commit()
    
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
        start_time = time.time()
        
        while True:
            with self._lock:
                # Get oldest unconsumed message
                cursor = self._conn.execute(
                    f'''SELECT id, message FROM queue_{self._safe_name} 
                        WHERE consumed = 0 
                        ORDER BY id ASC 
                        LIMIT 1'''
                )
                row = cursor.fetchone()
                
                if row:
                    msg_id, message_json = row
                    # Mark as consumed
                    self._conn.execute(
                        f'UPDATE queue_{self._safe_name} SET consumed = 1 WHERE id = ?',
                        (msg_id,)
                    )
                    self._conn.commit()
                    return json.loads(message_json)
            
            # Check timeout
            if timeout is not None:
                if timeout == 0:
                    return None
                elapsed = time.time() - start_time
                if elapsed >= timeout:
                    return None
            
            # Wait a bit before retrying
            time.sleep(0.01)
    
    def size(self) -> int:
        """
        Get the current queue size.
        
        Returns:
            Number of unconsumed messages in the queue
        """
        with self._lock:
            cursor = self._conn.execute(
                f'SELECT COUNT(*) FROM queue_{self._safe_name} WHERE consumed = 0'
            )
            return cursor.fetchone()[0]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """
        Get message history.
        
        Returns:
            List of all messages that have been enqueued
        """
        with self._lock:
            cursor = self._conn.execute(
                f'SELECT message FROM queue_{self._safe_name}_history ORDER BY id ASC'
            )
            return [json.loads(row[0]) for row in cursor.fetchall()]
    
    def clear(self) -> None:
        """Clear all messages from the queue."""
        with self._lock:
            self._conn.execute(f'DELETE FROM queue_{self._safe_name}')
            self._conn.commit()
    
    def clear_history(self) -> None:
        """Clear message history."""
        with self._lock:
            self._conn.execute(f'DELETE FROM queue_{self._safe_name}_history')
            self._conn.commit()
    
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self._conn.close()
    
    def __repr__(self) -> str:
        try:
            size = self.size()
            return f"SQLiteQueue(name={self.name}, size={size})"
        except:
            return f"SQLiteQueue(name={self.name})"


class SQLiteQueueManager(QueueManager):
    """
    SQLite queue manager.
    
    Manages multiple named SQLite queues.
    
    Attributes:
        db_path: Path to SQLite database file
    """
    
    def __init__(self, db_path: str = "idtf_queue.db"):
        """
        Initialize SQLite queue manager.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._queues: Dict[str, SQLiteQueue] = {}
        self._lock = Lock()
    
    def get_queue(self, name: str) -> SQLiteQueue:
        """
        Get or create a queue by name.
        
        Args:
            name: Queue name
        
        Returns:
            SQLiteQueue instance
        """
        with self._lock:
            if name not in self._queues:
                self._queues[name] = SQLiteQueue(name, self.db_path)
            return self._queues[name]
    
    def delete_queue(self, name: str) -> None:
        """
        Delete a queue by name.
        
        Args:
            name: Queue name
        """
        with self._lock:
            if name in self._queues:
                queue = self._queues[name]
                # Drop tables
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute(f'DROP TABLE IF EXISTS queue_{name}')
                    conn.execute(f'DROP TABLE IF EXISTS queue_{name}_history')
                    conn.commit()
                del self._queues[name]
    
    def list_queues(self) -> List[str]:
        """
        List all queue names.
        
        Returns:
            List of queue names
        """
        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'queue_%'"
                )
                # Extract queue names from table names
                queue_names = set()
                for row in cursor.fetchall():
                    table_name = row[0]
                    if not table_name.endswith('_history'):
                        # Remove 'queue_' prefix
                        queue_name = table_name[6:]
                        queue_names.add(queue_name)
                return sorted(list(queue_names))
    
    def __repr__(self) -> str:
        return f"SQLiteQueueManager(queues={len(self._queues)})"


# Demo
if __name__ == "__main__":
    print("=" * 80)
    print("SQLite Queue Demo")
    print("=" * 80)
    
    # Create queue manager
    manager = SQLiteQueueManager(":memory:")
    print(f"\nCreated queue manager: {manager}")
    
    # Get a queue
    queue = manager.get_queue("test_queue")
    print(f"Created queue: {queue}")
    
    # Put messages
    print("\nPutting messages...")
    for i in range(5):
        msg = {
            "id": i,
            "type": "test",
            "data": f"Message {i}",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        queue.put(msg)
        print(f"  Put: {msg}")
    
    print(f"\nQueue size: {queue.size()}")
    
    # Get messages
    print("\nGetting messages...")
    while queue.size() > 0:
        msg = queue.get(timeout=1.0)
        if msg:
            print(f"  Got: {msg}")
    
    print(f"\nQueue size: {queue.size()}")
    
    # Get history
    print("\nMessage history:")
    for msg in queue.get_history():
        print(f"  {msg}")
    
    # List queues
    print(f"\nAll queues: {manager.list_queues()}")
    
    print("\nDemo complete!")

