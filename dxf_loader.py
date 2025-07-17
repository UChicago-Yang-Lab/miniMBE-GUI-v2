#TODO:
# - Why are the Arc & Circle code done in a way where it's a regular list with an array of nparrays inside. why can't it just be  alist of nparrays
# - The Arc & Circle to my knowledge both use the OCS coordinate system while the LINE uses WCS. Check if this could be a potential problem and maybe just convert to be safe


"""Lightweight DXF loading helper."""
from __future__ import annotations

from typing import Iterable, List
import numpy as np
import math
import ezdxf
#-------------------------------------- Code Copied from Mini-MBE GUI #1 Attempt

def round_point(pt, decimals=6):
    """Round an (x, y) tuple to the specified number of decimals."""
    # Skip rounding for tiny geometries to avoid collapse
    if abs(pt[0]) < 0.001 or abs(pt[1]) < 0.001:
        return (pt[0], pt[1])
    return (round(pt[0], decimals), round(pt[1], decimals))


def generate_points_from_line(start, end, resolution=1.0, use_interpolation=True):
    """
    Interpolates points along a line from start to end.
    If use_interpolation is False, returns just the endpoints.
    """
    start = round_point(start)
    end = round_point(end)
    if not use_interpolation:
        return [start, end]
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy)
    if length <= resolution:
        return [start, end]
    num_segments = math.ceil(length / resolution)
    points = []
    for i in range(num_segments + 1):
        t = i / num_segments
        x = start[0] + dx * t
        y = start[1] + dy * t
        points.append(round_point((x, y)))
    return points


# method taken from part of og Mini-MBE GUI code; should help with line drawing but seperated into own method for organization
def lines_to_paths(line_endpoints:list):
    paths = []
    if line_endpoints:
        current_path = []
        used_lines = set()
        
        # Start with first line
        current_path.append(line_endpoints[0][0])
        current_path.append(line_endpoints[0][1])
        used_lines.add(0)
        
        while len(used_lines) < len(line_endpoints):
            found_connection = False
            current_end = current_path[-1]
            
            # Look for connecting line with higher precision
            for i, (start, end) in enumerate(line_endpoints):
                if i in used_lines:
                    continue
                
                # Use tighter tolerance for small geometries
                tolerance = 1e-9 if max(abs(current_end[0]), abs(current_end[1])) < 0.1 else 1e-6
                
                if math.dist(current_end, start) < tolerance:  # Connect to start
                    current_path.append(end)
                    used_lines.add(i)
                    found_connection = True
                    break
                elif math.dist(current_end, end) < tolerance:  # Connect to end
                    current_path.append(start)
                    used_lines.add(i)
                    found_connection = True
                    break
            
            if not found_connection:
                # Start new path if no connection found
                paths.append(current_path)
                remaining = set(range(len(line_endpoints))) - used_lines
                if remaining:
                    next_line = min(remaining)
                    current_path = list(line_endpoints[next_line])
                    used_lines.add(next_line)
                    
        paths.append(current_path) 

# ---------------------------------------------------------------------- End Code From Original Mini-MBE GUI Version


def load_dxf(path: str) -> list[np.ndarray]:
    print("is my debugging printing?") #debug
    """Load a DXF file and return a list of ``(N, 2)`` arrays."""
    doc = ezdxf.readfile(path)
    msp = doc.modelspace()
    #Should msp be purged first to remove destroyed/empty entities to prevent wasting time 
    shapes: list[np.ndarray] = []
    
    for entity in msp:
        print(f"{entity}\n") #debug
        kind = entity.dxftype()
        if kind in {"LWPOLYLINE", "POLYLINE"}:
            
            try:
                points = entity.get_points("xy")
            except AttributeError:
                points = [(v.dxf.x, v.dxf.y) for v in entity.vertices()]
            arr = np.array([[p[0], p[1]] for p in points], dtype=float)
            shapes.append(arr)
        elif kind =="LINE":
            #A LINE in dxf only has two properties: start and end
            #print('line appended') # debug
            #try:
            start_point = entity.dxf.start 
            end_point = entity.dxf.end
            print(entity.dxf.extrusion)
            arr = np.array([[start_point[0],end_point[0]],[start_point[1],end_point[1]]])
            '''except AttributeError:
                points = [(v.dxf.x, v.dxf.y) for v in entity.vertices()]
                arr = np.array([[p[0], p[1]] for p in points], dtype=float)'''
            shapes.append(arr)

            
        elif kind == "ARC":
            center = np.array([entity.dxf.center[0],entity.dxf.center[1]], dtype=float)
            radius = float(entity.dxf.radius)
            start = np.radians(float(entity.dxf.start_angle))
            end = np.radians(float(entity.dxf.end_angle))
            # ensure correct direction and resolution
            steps = max(int(abs(end - start) / (np.pi / 90)), 2)
            angles = np.linspace(start, end, steps)
            x = center[0] + radius * np.cos(angles)
            y = center[1] + radius * np.sin(angles)
            shapes.append(np.column_stack([x, y]))
        elif kind == "CIRCLE":
            print('circ appended') # debug
            center = np.array([entity.dxf.center[0],entity.dxf.center[1]], dtype=float)

            radius = float(entity.dxf.radius)
            angles = np.linspace(0, 2 * np.pi, 90)
            x = center[0] + radius * np.cos(angles)
            y = center[1] + radius * np.sin(angles)
            shapes.append(np.column_stack([x, y]))

    return shapes


