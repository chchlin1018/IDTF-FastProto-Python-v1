"""
Geom - Bounding box utilities (AABB and OBB)
"""

from typing import List, Tuple, Optional
import numpy as np


class AABB:
    """
    Axis-Aligned Bounding Box (AABB).
    
    Attributes:
        min: Minimum point [x, y, z]
        max: Maximum point [x, y, z]
    """
    
    def __init__(self, min_point: List[float], max_point: List[float]):
        """
        Initialize an AABB.
        
        Args:
            min_point: Minimum point [x, y, z]
            max_point: Maximum point [x, y, z]
        """
        self.min = np.array(min_point, dtype=float)
        self.max = np.array(max_point, dtype=float)
    
    def center(self) -> np.ndarray:
        """Get the center point of the AABB."""
        return (self.min + self.max) / 2.0
    
    def size(self) -> np.ndarray:
        """Get the size (dimensions) of the AABB."""
        return self.max - self.min
    
    def volume(self) -> float:
        """Calculate the volume of the AABB."""
        size = self.size()
        return float(size[0] * size[1] * size[2])
    
    def contains_point(self, point: List[float]) -> bool:
        """
        Check if a point is inside the AABB.
        
        Args:
            point: Point [x, y, z]
        
        Returns:
            bool: True if the point is inside, False otherwise
        """
        p = np.array(point, dtype=float)
        return np.all(p >= self.min) and np.all(p <= self.max)
    
    def intersects(self, other: "AABB") -> bool:
        """
        Check if this AABB intersects with another AABB.
        
        Args:
            other: Another AABB
        
        Returns:
            bool: True if they intersect, False otherwise
        """
        return np.all(self.min <= other.max) and np.all(self.max >= other.min)
    
    def expand(self, distance: float) -> "AABB":
        """
        Expand the AABB by a given distance in all directions.
        
        Args:
            distance: Distance to expand
        
        Returns:
            AABB: A new expanded AABB
        """
        return AABB(
            (self.min - distance).tolist(),
            (self.max + distance).tolist()
        )
    
    def merge(self, other: "AABB") -> "AABB":
        """
        Merge this AABB with another AABB.
        
        Args:
            other: Another AABB
        
        Returns:
            AABB: A new AABB that encompasses both
        """
        return AABB(
            np.minimum(self.min, other.min).tolist(),
            np.maximum(self.max, other.max).tolist()
        )
    
    def to_dict(self) -> dict:
        """Convert AABB to dictionary."""
        return {
            "type": "AABB",
            "min": self.min.tolist(),
            "max": self.max.tolist()
        }
    
    @classmethod
    def from_points(cls, points: List[List[float]]) -> "AABB":
        """
        Create an AABB from a list of points.
        
        Args:
            points: List of points [[x, y, z], ...]
        
        Returns:
            AABB: The bounding AABB
        """
        points_array = np.array(points, dtype=float)
        min_point = np.min(points_array, axis=0)
        max_point = np.max(points_array, axis=0)
        return cls(min_point.tolist(), max_point.tolist())
    
    def __repr__(self):
        return f"AABB(min={self.min.tolist()}, max={self.max.tolist()})"


class OBB:
    """
    Oriented Bounding Box (OBB).
    
    Attributes:
        center: Center point [x, y, z]
        axes: Three orthonormal axes as a 3x3 matrix
        extents: Half-extents along each axis [ex, ey, ez]
    """
    
    def __init__(self, center: List[float], axes: List[List[float]], extents: List[float]):
        """
        Initialize an OBB.
        
        Args:
            center: Center point [x, y, z]
            axes: Three orthonormal axes as a 3x3 matrix [[ax1, ay1, az1], [ax2, ay2, az2], [ax3, ay3, az3]]
            extents: Half-extents along each axis [ex, ey, ez]
        """
        self.center = np.array(center, dtype=float)
        self.axes = np.array(axes, dtype=float)  # 3x3 matrix
        self.extents = np.array(extents, dtype=float)
    
    def volume(self) -> float:
        """Calculate the volume of the OBB."""
        return float(8.0 * self.extents[0] * self.extents[1] * self.extents[2])
    
    def to_aabb(self) -> AABB:
        """
        Convert OBB to an axis-aligned bounding box (AABB).
        
        Returns:
            AABB: The bounding AABB
        """
        # Get all 8 corners of the OBB
        corners = self.get_corners()
        return AABB.from_points(corners)
    
    def get_corners(self) -> List[List[float]]:
        """
        Get the 8 corner points of the OBB.
        
        Returns:
            List[List[float]]: List of 8 corner points
        """
        corners = []
        for i in [-1, 1]:
            for j in [-1, 1]:
                for k in [-1, 1]:
                    offset = (
                        i * self.extents[0] * self.axes[0] +
                        j * self.extents[1] * self.axes[1] +
                        k * self.extents[2] * self.axes[2]
                    )
                    corner = self.center + offset
                    corners.append(corner.tolist())
        return corners
    
    def to_dict(self) -> dict:
        """Convert OBB to dictionary."""
        return {
            "type": "OBB",
            "center": self.center.tolist(),
            "axes": self.axes.tolist(),
            "extents": self.extents.tolist()
        }
    
    def __repr__(self):
        return f"OBB(center={self.center.tolist()}, extents={self.extents.tolist()})"


if __name__ == '__main__':
    print("=== Geom Bounding Box Utilities Demo ===\n")
    
    # AABB Demo
    print("--- AABB Demo ---")
    aabb1 = AABB([0.0, 0.0, 0.0], [10.0, 10.0, 10.0])
    print(f"AABB1: {aabb1}")
    print(f"Center: {aabb1.center()}")
    print(f"Size: {aabb1.size()}")
    print(f"Volume: {aabb1.volume()}")
    print()
    
    # Point containment
    print("--- Point Containment ---")
    point_inside = [5.0, 5.0, 5.0]
    point_outside = [15.0, 5.0, 5.0]
    print(f"Point {point_inside} inside AABB1: {aabb1.contains_point(point_inside)}")
    print(f"Point {point_outside} inside AABB1: {aabb1.contains_point(point_outside)}")
    print()
    
    # AABB intersection
    print("--- AABB Intersection ---")
    aabb2 = AABB([5.0, 5.0, 5.0], [15.0, 15.0, 15.0])
    aabb3 = AABB([20.0, 20.0, 20.0], [30.0, 30.0, 30.0])
    print(f"AABB1 intersects AABB2: {aabb1.intersects(aabb2)}")
    print(f"AABB1 intersects AABB3: {aabb1.intersects(aabb3)}")
    print()
    
    # AABB expansion
    print("--- AABB Expansion ---")
    expanded_aabb = aabb1.expand(2.0)
    print(f"Original AABB1: {aabb1}")
    print(f"Expanded AABB1 (by 2.0): {expanded_aabb}")
    print()
    
    # AABB merge
    print("--- AABB Merge ---")
    merged_aabb = aabb1.merge(aabb2)
    print(f"Merged AABB (AABB1 + AABB2): {merged_aabb}")
    print()
    
    # AABB from points
    print("--- AABB from Points ---")
    points = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0], [7.0, 8.0, 9.0]]
    aabb_from_points = AABB.from_points(points)
    print(f"Points: {points}")
    print(f"AABB from points: {aabb_from_points}")
    print()
    
    # OBB Demo
    print("--- OBB Demo ---")
    obb = OBB(
        center=[5.0, 5.0, 5.0],
        axes=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],  # Identity (axis-aligned)
        extents=[2.0, 3.0, 4.0]
    )
    print(f"OBB: {obb}")
    print(f"Volume: {obb.volume()}")
    print(f"Corners: {obb.get_corners()}")
    print(f"OBB as AABB: {obb.to_aabb()}")
    print()

