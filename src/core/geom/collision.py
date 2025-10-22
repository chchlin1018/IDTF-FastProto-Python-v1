"""
Geom - Collision detection utilities using PyBullet
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from .bbox import AABB


class CollisionChecker:
    """
    Collision checker using AABB for fast broad-phase detection.
    Can be extended with PyBullet for precise mesh-level collision detection.
    """
    
    def __init__(self, clearance_distance: float = 0.0):
        """
        Initialize collision checker.
        
        Args:
            clearance_distance: Minimum clearance distance between objects (in meters)
        """
        self.clearance_distance = clearance_distance
    
    def check_aabb_collision(
        self,
        aabb1: AABB,
        aabb2: AABB,
        include_clearance: bool = True
    ) -> bool:
        """
        Check collision between two AABBs.
        
        Args:
            aabb1: First AABB
            aabb2: Second AABB
            include_clearance: Whether to include clearance distance
        
        Returns:
            bool: True if collision detected, False otherwise
        """
        if include_clearance and self.clearance_distance > 0:
            expanded_aabb1 = aabb1.expand(self.clearance_distance)
            return expanded_aabb1.intersects(aabb2)
        else:
            return aabb1.intersects(aabb2)
    
    def check_point_in_aabb(
        self,
        point: List[float],
        aabb: AABB,
        include_clearance: bool = True
    ) -> bool:
        """
        Check if a point is inside an AABB (with optional clearance).
        
        Args:
            point: Point [x, y, z]
            aabb: AABB to check
            include_clearance: Whether to include clearance distance
        
        Returns:
            bool: True if point is inside, False otherwise
        """
        if include_clearance and self.clearance_distance > 0:
            expanded_aabb = aabb.expand(self.clearance_distance)
            return expanded_aabb.contains_point(point)
        else:
            return aabb.contains_point(point)
    
    def find_collisions(
        self,
        aabbs: Dict[str, AABB]
    ) -> List[Tuple[str, str]]:
        """
        Find all pairwise collisions among a set of AABBs.
        
        Args:
            aabbs: Dictionary mapping instance IDs to AABBs
        
        Returns:
            List[Tuple[str, str]]: List of colliding instance ID pairs
        """
        collisions = []
        instance_ids = list(aabbs.keys())
        
        for i in range(len(instance_ids)):
            for j in range(i + 1, len(instance_ids)):
                id1 = instance_ids[i]
                id2 = instance_ids[j]
                
                if self.check_aabb_collision(aabbs[id1], aabbs[id2]):
                    collisions.append((id1, id2))
        
        return collisions


class PyBulletCollisionChecker:
    """
    Advanced collision checker using PyBullet for precise mesh-level collision detection.
    
    Note: This class requires PyBullet to be installed.
    Install with: pip install pybullet
    """
    
    def __init__(self, clearance_distance: float = 0.0, use_gui: bool = False):
        """
        Initialize PyBullet collision checker.
        
        Args:
            clearance_distance: Minimum clearance distance between objects (in meters)
            use_gui: Whether to use PyBullet GUI (for debugging)
        """
        try:
            import pybullet as p
            import pybullet_data
            self.p = p
            self.pybullet_data = pybullet_data
        except ImportError:
            raise ImportError("PyBullet is not installed. Install with: pip install pybullet")
        
        self.clearance_distance = clearance_distance
        self.use_gui = use_gui
        
        # Initialize PyBullet
        if use_gui:
            self.physics_client = self.p.connect(self.p.GUI)
        else:
            self.physics_client = self.p.connect(self.p.DIRECT)
        
        self.p.setAdditionalSearchPath(self.pybullet_data.getDataPath())
        
        # Dictionary to store loaded collision objects
        self.collision_objects: Dict[str, int] = {}
    
    def add_box_collision_object(
        self,
        instance_id: str,
        position: List[float],
        half_extents: List[float],
        orientation: Optional[List[float]] = None
    ):
        """
        Add a box collision object.
        
        Args:
            instance_id: Unique identifier for the object
            position: Position [x, y, z]
            half_extents: Half extents [ex, ey, ez]
            orientation: Quaternion [x, y, z, w] (optional, default: [0, 0, 0, 1])
        """
        if orientation is None:
            orientation = [0, 0, 0, 1]
        
        collision_shape = self.p.createCollisionShape(
            self.p.GEOM_BOX,
            halfExtents=half_extents
        )
        
        body_id = self.p.createMultiBody(
            baseMass=0,  # Static object
            baseCollisionShapeIndex=collision_shape,
            basePosition=position,
            baseOrientation=orientation
        )
        
        self.collision_objects[instance_id] = body_id
    
    def add_sphere_collision_object(
        self,
        instance_id: str,
        position: List[float],
        radius: float
    ):
        """
        Add a sphere collision object.
        
        Args:
            instance_id: Unique identifier for the object
            position: Position [x, y, z]
            radius: Sphere radius
        """
        collision_shape = self.p.createCollisionShape(
            self.p.GEOM_SPHERE,
            radius=radius
        )
        
        body_id = self.p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=collision_shape,
            basePosition=position
        )
        
        self.collision_objects[instance_id] = body_id
    
    def add_mesh_collision_object(
        self,
        instance_id: str,
        mesh_file_path: str,
        position: List[float],
        scale: List[float] = None,
        orientation: Optional[List[float]] = None
    ):
        """
        Add a mesh collision object from a file.
        
        Args:
            instance_id: Unique identifier for the object
            mesh_file_path: Path to mesh file (.obj, .stl, etc.)
            position: Position [x, y, z]
            scale: Scale [sx, sy, sz] (optional, default: [1, 1, 1])
            orientation: Quaternion [x, y, z, w] (optional, default: [0, 0, 0, 1])
        """
        if scale is None:
            scale = [1, 1, 1]
        if orientation is None:
            orientation = [0, 0, 0, 1]
        
        collision_shape = self.p.createCollisionShape(
            self.p.GEOM_MESH,
            fileName=mesh_file_path,
            meshScale=scale
        )
        
        body_id = self.p.createMultiBody(
            baseMass=0,
            baseCollisionShapeIndex=collision_shape,
            basePosition=position,
            baseOrientation=orientation
        )
        
        self.collision_objects[instance_id] = body_id
    
    def remove_collision_object(self, instance_id: str):
        """
        Remove a collision object.
        
        Args:
            instance_id: Unique identifier of the object to remove
        """
        if instance_id in self.collision_objects:
            body_id = self.collision_objects[instance_id]
            self.p.removeBody(body_id)
            del self.collision_objects[instance_id]
    
    def check_collision(
        self,
        instance_id1: str,
        instance_id2: str,
        max_distance: Optional[float] = None
    ) -> bool:
        """
        Check collision between two objects.
        
        Args:
            instance_id1: First object ID
            instance_id2: Second object ID
            max_distance: Maximum distance to consider as collision (optional)
        
        Returns:
            bool: True if collision detected, False otherwise
        """
        if instance_id1 not in self.collision_objects or instance_id2 not in self.collision_objects:
            return False
        
        body_id1 = self.collision_objects[instance_id1]
        body_id2 = self.collision_objects[instance_id2]
        
        if max_distance is None:
            max_distance = self.clearance_distance
        
        contact_points = self.p.getClosestPoints(
            bodyA=body_id1,
            bodyB=body_id2,
            distance=max_distance
        )
        
        return len(contact_points) > 0
    
    def find_all_collisions(self) -> List[Tuple[str, str]]:
        """
        Find all pairwise collisions among loaded objects.
        
        Returns:
            List[Tuple[str, str]]: List of colliding instance ID pairs
        """
        collisions = []
        instance_ids = list(self.collision_objects.keys())
        
        for i in range(len(instance_ids)):
            for j in range(i + 1, len(instance_ids)):
                id1 = instance_ids[i]
                id2 = instance_ids[j]
                
                if self.check_collision(id1, id2):
                    collisions.append((id1, id2))
        
        return collisions
    
    def get_closest_distance(
        self,
        instance_id1: str,
        instance_id2: str
    ) -> Optional[float]:
        """
        Get the closest distance between two objects.
        
        Args:
            instance_id1: First object ID
            instance_id2: Second object ID
        
        Returns:
            Optional[float]: Closest distance, or None if objects not found
        """
        if instance_id1 not in self.collision_objects or instance_id2 not in self.collision_objects:
            return None
        
        body_id1 = self.collision_objects[instance_id1]
        body_id2 = self.collision_objects[instance_id2]
        
        contact_points = self.p.getClosestPoints(
            bodyA=body_id1,
            bodyB=body_id2,
            distance=100.0  # Large distance to ensure we get a result
        )
        
        if contact_points:
            return contact_points[0][8]  # Contact distance
        
        return None
    
    def cleanup(self):
        """Disconnect from PyBullet and clean up resources."""
        self.p.disconnect()


if __name__ == '__main__':
    print("=== Geom Collision Detection Utilities Demo ===\n")
    
    # AABB Collision Checker Demo
    print("--- AABB Collision Checker Demo ---")
    checker = CollisionChecker(clearance_distance=0.5)
    
    aabb1 = AABB([0.0, 0.0, 0.0], [10.0, 10.0, 10.0])
    aabb2 = AABB([9.0, 9.0, 9.0], [15.0, 15.0, 15.0])
    aabb3 = AABB([20.0, 20.0, 20.0], [30.0, 30.0, 30.0])
    
    print(f"AABB1 vs AABB2 (with clearance): {checker.check_aabb_collision(aabb1, aabb2)}")
    print(f"AABB1 vs AABB3 (with clearance): {checker.check_aabb_collision(aabb1, aabb3)}")
    print()
    
    # Find all collisions
    print("--- Find All Collisions ---")
    aabbs = {
        "asset_001": aabb1,
        "asset_002": aabb2,
        "asset_003": aabb3
    }
    collisions = checker.find_collisions(aabbs)
    print(f"Collisions: {collisions}")
    print()
    
    # PyBullet Collision Checker Demo
    print("--- PyBullet Collision Checker Demo ---")
    try:
        pb_checker = PyBulletCollisionChecker(clearance_distance=0.1, use_gui=False)
        
        # Add collision objects
        pb_checker.add_box_collision_object("box1", [0, 0, 0], [1, 1, 1])
        pb_checker.add_box_collision_object("box2", [1.5, 0, 0], [1, 1, 1])
        pb_checker.add_sphere_collision_object("sphere1", [5, 0, 0], 1.0)
        
        # Check collisions
        print(f"box1 vs box2: {pb_checker.check_collision('box1', 'box2')}")
        print(f"box1 vs sphere1: {pb_checker.check_collision('box1', 'sphere1')}")
        
        # Get closest distance
        distance = pb_checker.get_closest_distance('box1', 'box2')
        print(f"Closest distance (box1 to box2): {distance}")
        
        # Find all collisions
        all_collisions = pb_checker.find_all_collisions()
        print(f"All collisions: {all_collisions}")
        
        # Cleanup
        pb_checker.cleanup()
        print("\nPyBullet demo completed successfully.")
        
    except ImportError as e:
        print(f"PyBullet demo skipped: {e}")
        print("Install PyBullet with: pip install pybullet")
    
    print()

