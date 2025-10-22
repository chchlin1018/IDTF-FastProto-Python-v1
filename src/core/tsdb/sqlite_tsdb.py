"""
TSDB - SQLite implementation (for MVP and testing)
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from .interfaces import ITSDB, TagValue, AggregatedValue, AggregationFunction


class SQLiteTSDB(ITSDB):
    """
    SQLite-based time-series database implementation.
    
    Suitable for MVP, small-scale deployments, and testing.
    Data is persisted to a SQLite database file.
    """
    
    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize SQLite TSDB.
        
        Args:
            db_path: Path to SQLite database file (default: ":memory:" for in-memory database)
        """
        self.db_path = db_path
        
        if db_path != ":memory:":
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
    
    def _create_tables(self):
        """Create database tables."""
        cursor = self.conn.cursor()
        
        # Create tag_values table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tag_values (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tag_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                value REAL,
                quality INTEGER DEFAULT 100,
                source TEXT DEFAULT ''
            )
        """)
        
        # Create index on tag_id and timestamp for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_tag_timestamp 
            ON tag_values(tag_id, timestamp)
        """)
        
        self.conn.commit()
    
    def write_tag_value(self, tag_value: TagValue) -> bool:
        """Write a single tag value."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO tag_values (tag_id, timestamp, value, quality, source)
                VALUES (?, ?, ?, ?, ?)
            """, (
                tag_value.tag_id,
                tag_value.timestamp,
                tag_value.value,
                tag_value.quality,
                tag_value.source
            ))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error writing tag value: {e}")
            return False
    
    def write_tag_values(self, tag_values: List[TagValue]) -> int:
        """Write multiple tag values (batch write)."""
        count = 0
        cursor = self.conn.cursor()
        
        try:
            for tag_value in tag_values:
                cursor.execute("""
                    INSERT INTO tag_values (tag_id, timestamp, value, quality, source)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    tag_value.tag_id,
                    tag_value.timestamp,
                    tag_value.value,
                    tag_value.quality,
                    tag_value.source
                ))
                count += 1
            
            self.conn.commit()
        except Exception as e:
            print(f"Error in batch write: {e}")
            self.conn.rollback()
        
        return count
    
    def query_tag_values(
        self,
        tag_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[TagValue]:
        """Query tag values within a time range."""
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM tag_values WHERE tag_id = ?"
        params = [tag_id]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat() + "Z")
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat() + "Z")
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [
            TagValue(
                tag_id=row["tag_id"],
                timestamp=row["timestamp"],
                value=row["value"],
                quality=row["quality"],
                source=row["source"]
            )
            for row in rows
        ]
    
    def query_latest_value(self, tag_id: str) -> Optional[TagValue]:
        """Query the latest value for a tag."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT * FROM tag_values 
            WHERE tag_id = ? 
            ORDER BY timestamp DESC 
            LIMIT 1
        """, (tag_id,))
        
        row = cursor.fetchone()
        if row:
            return TagValue(
                tag_id=row["tag_id"],
                timestamp=row["timestamp"],
                value=row["value"],
                quality=row["quality"],
                source=row["source"]
            )
        return None
    
    def query_aggregated_values(
        self,
        tag_id: str,
        start_time: datetime,
        end_time: datetime,
        function: AggregationFunction,
        interval_seconds: int
    ) -> List[AggregatedValue]:
        """Query aggregated tag values."""
        # This is a simplified implementation
        # For production, use window functions or time-bucket functions
        
        cursor = self.conn.cursor()
        
        # Map aggregation function to SQL
        agg_func_map = {
            AggregationFunction.AVG: "AVG",
            AggregationFunction.MIN: "MIN",
            AggregationFunction.MAX: "MAX",
            AggregationFunction.SUM: "SUM",
            AggregationFunction.COUNT: "COUNT",
            AggregationFunction.FIRST: "MIN",  # Simplified
            AggregationFunction.LAST: "MAX",   # Simplified
            AggregationFunction.STDDEV: "AVG"  # SQLite doesn't have STDDEV, use AVG as placeholder
        }
        
        sql_func = agg_func_map.get(function, "AVG")
        
        # Simple aggregation over the entire time range
        # For proper time-bucketing, use DuckDB or TDEngine
        cursor.execute(f"""
            SELECT 
                tag_id,
                MIN(timestamp) as start_time,
                MAX(timestamp) as end_time,
                {sql_func}(value) as agg_value,
                COUNT(*) as count
            FROM tag_values
            WHERE tag_id = ? AND timestamp >= ? AND timestamp <= ?
            GROUP BY tag_id
        """, (tag_id, start_time.isoformat() + "Z", end_time.isoformat() + "Z"))
        
        row = cursor.fetchone()
        if row:
            return [
                AggregatedValue(
                    tag_id=row["tag_id"],
                    start_time=row["start_time"],
                    end_time=row["end_time"],
                    function=function,
                    value=row["agg_value"],
                    count=row["count"]
                )
            ]
        return []
    
    def delete_tag_values(
        self,
        tag_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """Delete tag values within a time range."""
        cursor = self.conn.cursor()
        
        query = "DELETE FROM tag_values WHERE tag_id = ?"
        params = [tag_id]
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time.isoformat() + "Z")
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time.isoformat() + "Z")
        
        cursor.execute(query, params)
        self.conn.commit()
        
        return cursor.rowcount
    
    def get_stats(self) -> Dict[str, Any]:
        """Get TSDB statistics."""
        cursor = self.conn.cursor()
        
        # Total values
        cursor.execute("SELECT COUNT(*) as total_values FROM tag_values")
        total_values = cursor.fetchone()["total_values"]
        
        # Unique tags
        cursor.execute("SELECT COUNT(DISTINCT tag_id) as unique_tags FROM tag_values")
        unique_tags = cursor.fetchone()["unique_tags"]
        
        # Database size (for file-based databases)
        db_size = 0
        if self.db_path != ":memory:":
            db_path = Path(self.db_path)
            if db_path.exists():
                db_size = db_path.stat().st_size
        
        return {
            "total_values": total_values,
            "unique_tags": unique_tags,
            "db_size_bytes": db_size,
            "db_path": self.db_path
        }
    
    def close(self):
        """Close the database connection."""
        self.conn.close()


if __name__ == '__main__':
    from datetime import datetime, timedelta
    from ..tags.id_generator import generate_uuidv7
    import time
    
    print("=== SQLite TSDB Demo ===\n")
    
    # Create in-memory TSDB
    tsdb = SQLiteTSDB(":memory:")
    
    # Generate sample tag IDs
    tag_id_temp = generate_uuidv7()
    tag_id_pressure = generate_uuidv7()
    
    # Write single tag value
    print("--- Writing Single Tag Value ---")
    tag_value = TagValue(
        tag_id=tag_id_temp,
        timestamp=datetime.utcnow().isoformat() + "Z",
        value=25.5,
        quality=100,
        source="PLC_001"
    )
    tsdb.write_tag_value(tag_value)
    print(f"Written tag value: {tag_value.tag_id} = {tag_value.value}")
    print()
    
    # Write batch tag values
    print("--- Writing Batch Tag Values ---")
    tag_values = []
    base_time = datetime.utcnow()
    
    for i in range(10):
        timestamp = (base_time + timedelta(seconds=i)).isoformat() + "Z"
        
        # Temperature values
        tag_values.append(TagValue(
            tag_id=tag_id_temp,
            timestamp=timestamp,
            value=25.0 + i * 0.5,
            quality=100,
            source="PLC_001"
        ))
        
        # Pressure values
        tag_values.append(TagValue(
            tag_id=tag_id_pressure,
            timestamp=timestamp,
            value=100.0 + i * 2.0,
            quality=100,
            source="PLC_001"
        ))
    
    written_count = tsdb.write_tag_values(tag_values)
    print(f"Written {written_count} tag values")
    print()
    
    # Query latest value
    print("--- Querying Latest Value ---")
    latest_temp = tsdb.query_latest_value(tag_id_temp)
    if latest_temp:
        print(f"Latest temperature: {latest_temp.value} at {latest_temp.timestamp}")
    print()
    
    # Query tag values
    print("--- Querying Tag Values ---")
    temp_values = tsdb.query_tag_values(tag_id_temp, limit=5)
    print(f"Retrieved {len(temp_values)} temperature values:")
    for tv in temp_values[:3]:
        print(f"  {tv.timestamp}: {tv.value}")
    print()
    
    # Query aggregated values
    print("--- Querying Aggregated Values ---")
    agg_values = tsdb.query_aggregated_values(
        tag_id_temp,
        base_time,
        base_time + timedelta(seconds=10),
        AggregationFunction.AVG,
        interval_seconds=60
    )
    if agg_values:
        agg = agg_values[0]
        print(f"Average temperature: {agg.value} (count: {agg.count})")
    print()
    
    # Get statistics
    print("--- TSDB Statistics ---")
    stats = tsdb.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    print()
    
    # Delete tag values
    print("--- Deleting Tag Values ---")
    deleted_count = tsdb.delete_tag_values(tag_id_pressure)
    print(f"Deleted {deleted_count} pressure values")
    print()
    
    # Final statistics
    print("--- Final Statistics ---")
    final_stats = tsdb.get_stats()
    print(f"Total values: {final_stats['total_values']}")
    print(f"Unique tags: {final_stats['unique_tags']}")
    print()
    
    # Close TSDB
    tsdb.close()
    print("TSDB closed.")

